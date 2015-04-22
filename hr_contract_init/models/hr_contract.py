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


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    @api.one
    def _get_wage(self, job_id=None):
        res = 0
        default = 0
        init = self.get_latest_initial_values()
        if job_id:
            catdata = self.env['hr.job'].browse(job_id).category_ids
        else:
            catdata = False
        if init is not None:
            for line in init.wage_ids:
                if job_id is not None and line.job_id.id == job_id:
                    res = line.starting_wage
                elif catdata:
                    cat_id = False
                    category_ids = [c.id for c in line.category_ids]
                    for ci in catdata:
                        if ci.id in category_ids:
                            cat_id = ci.id
                            break
                    if cat_id:
                        res = line.starting_wage
                if line.is_default and default == 0:
                    default = line.starting_wage
                if res != 0:
                    break
        self.wage = res != 0 and res or default

    @api.one
    def _get_struct(self):
        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.struct_id:
            res = init.struct_id.id
        self.struct_id = res

    @api.one
    def _get_trial_date_start(self, cr, uid, context=None):

        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            res = fields.Date.today()
        self.trial_date_start = res

    @api.one
    def _get_trial_date_end(self, cr, uid, context=None):

        res = False
        init = self.get_latest_initial_values(cr, uid, context=context)
        if init is not None and init.trial_period and init.trial_period > 0:
            res = fields.Date.today() + timedelta(days=init.trial_period)
        self.trial_date_end = res

    wage = fields.Float(string='Wage',
                        default="_get_wage",
                        digits_compute=dp.get_precision('Payroll'),
                        required=True,
                        help="Basic Salary of the employee")
    struct_id = fields.Many2one('hr.payroll.structure',
                                string='Salary Structure',
                                default="_get_struct")
    trial_date_start = fields.Date(string='Trial Start Date',
                                   default="_get_trial_date_start")
    trial_date_end = fields.Date(string='Trial End Date',
                                 default="_get_trial_date_end")

    @api.onchange('job_id')
    def onchange_job(self):
        self.ensure_one()
        if self.job_id:
            self.wage = self._get_wage(job_id=self.job_id)

    @api.onchange('trial_date_start')
    def onchange_trial(self):
        self.ensure_one()
        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            self.trial_date_end = self.trial_date_start + \
                                  timedelta(days=init.trial_period)

    @api.multi
    @api.returns('hr.contract.init')
    def get_latest_initial_values(self, date=None):
        """Return a record with an effective date before today_str
        but greater than all others
        """
        init_obj = self.env['hr.contract.init']
        if date is None:
            date = fields.Date.today()
        res = None
        init_ids = init_obj.search([('date', '<=', date),
                                    ('state', '=', 'approve')])
        for init in init_ids:
            if init.date <= date:
                if res is None:
                    res = init
                elif init.date > res.date:
                    res = init
        return res
