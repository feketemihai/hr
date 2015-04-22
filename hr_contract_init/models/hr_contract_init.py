# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp


class contract_init(models.Model):
    _name = 'hr.contract.init'
    _description = 'Initial Contract Settings'

    _inherit = 'ir.needaction_mixin'

    name = fields.Char(string='Name', required=True, readonly=True,
                       states={'draft': [('readonly', False)]})
    date = fields.Date(string='Effective Date', required=True,
                       readonly=True,
                       states={'draft': [('readonly', False)]})
    wage_ids = fields.One2many('hr.contract.init.wage', 'contract_init_id',
                               string='Starting Wages', readonly=True,
                               states={'draft': [('readonly', False)]})
    struct_id = fields.Many2one('hr.payroll.structure',
                                string='Payroll Structure',
                                readonly=True,
                                states={'draft': [('readonly', False)]})
    trial_period = fields.Integer(string='Trial Period', readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=0,
                                  help="Length of Trial Period, in days")
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('approve', 'Approved'),
                              ('decline', 'Declined')],
                             string='State',
                             readonly=True,
                             default='draft')

    # Return records with latest date first
    _order = 'date desc'

    @api.model
    def _needaction_domain_get(self):
        if self.env.user.has_group('base.group_hr_director'):
            domain = [('state', 'in', ['draft'])]
            return domain
        return False

    @api.multi
    def unlink(self):
        for contract in self:
            if contract.state in ['approve', 'decline']:
                raise Warning(_('You may not a delete a record that is not '
                                'in a "Draft" state'))
        return super(contract_init, self).unlink()

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})
        self.delete_workflow()
        self.create_workflow()
        return True

    @api.multi
    def state_approve(self):
        self.write({'state': 'approve'})
        return True

    @api.multi
    def state_decline(self):
        self.write({'state': 'decline'})
        return True


class init_wage(models.Model):
    _name = 'hr.contract.init.wage'
    _description = 'Starting Wages'

    job_id = fields.Many2one('hr.job', string='Job')
    starting_wage = fields.Float(string='Starting Wage',
                                 digits_compute=dp.get_precision('Payroll'),
                                 required=True),
    is_default = fields.Boolean(string='Use as Default',
                                help="Use as default wage")
    contract_init_id = fields.Many2one('hr.contract.init',
                                       string='Contract Settings')
    category_ids = fields.Many2many('hr.employee.category',
                                    'contract_init_category_rel',
                                    'contract_init_id',
                                    'category_id',
                                    string='Tags')

    @api.multi
    def _rec_message(self):
        self.ensure_one()
        return _('A Job Position cannot be referenced more than once in a '
                 'Contract Settings record.')

    _sql_constraints = [
        ('unique_job_cinit', 'UNIQUE(job_id,contract_init_id)', _rec_message),
    ]

    @api.multi
    def unlink(self):
        for wage in self:
            if not d.get('contract_init_id', False):
                continue
            if wage.contract_init_id.state in ['approve', 'decline']:
                raise Warning(_('You may not a delete a record that is not '
                                'in a "Draft" state'))
        return super(init_wage, self).unlink()
