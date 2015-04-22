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

from datetime import datetime, timedelta

from openerp import models, fields, api, exceptions, _

from openerp import netsvc
from openerp.addons import decimal_precision as dp
from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from openerp.tools.translate import _


class contract_init(orm.Model):

    _name = 'hr.contract.init'
    _description = 'Initial Contract Settings'

    _inherit = 'ir.needaction_mixin'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]},
        ),
        'date': fields.date(
            'Effective Date',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]},
        ),
        'wage_ids': fields.one2many(
            'hr.contract.init.wage',
            'contract_init_id',
            'Starting Wages', readonly=True,
            states={'draft': [('readonly', False)]},
        ),
        'struct_id': fields.many2one(
            'hr.payroll.structure',
            'Payroll Structure',
            readonly=True,
            states={'draft': [('readonly', False)]},
        ),
        'trial_period': fields.integer(
            'Trial Period',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Length of Trial Period, in days",
        ),
        'active': fields.boolean(
            'Active',
        ),
        'state': fields.selection(
            [
                ('draft', 'Draft'),
                ('approve', 'Approved'),
                ('decline', 'Declined'),
            ],
            'State',
            readonly=True,
        ),
    }

    _defaults = {
        'trial_period': 0,
        'active': True,
        'state': 'draft',
    }

    # Return records with latest date first
    _order = 'date desc'

    def _needaction_domain_get(self, cr, uid, context=None):

        users_obj = self.pool.get('res.users')

        if users_obj.has_group(cr, uid, 'base.group_hr_director'):
            domain = [('state', 'in', ['draft'])]
            return domain

        return False

    def unlink(self, cr, uid, ids, context=None):

        if isinstance(ids, (int, long)):
            ids = [ids]
        data = self.read(cr, uid, ids, ['state'], context=context)
        for d in data:
            if d['state'] in ['approve', 'decline']:
                raise orm.except_orm(
                    _('Error'),
                    _('You may not a delete a record that is not in a '
                      '"Draft" state')
                )
        return super(contract_init, self).unlink(cr, uid, ids, context=context)

    def set_to_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'draft',
        }, context=context)
        wf_service = netsvc.LocalService("workflow")
        for i in ids:
            wf_service.trg_delete(uid, 'hr.contract.init', i, cr)
            wf_service.trg_create(uid, 'hr.contract.init', i, cr)
        return True

    def state_approve(self, cr, uid, ids, context=None):

        self.write(cr, uid, ids, {'state': 'approve'}, context=context)
        return True

    def state_decline(self, cr, uid, ids, context=None):

        self.write(cr, uid, ids, {'state': 'decline'}, context=context)
        return True


class init_wage(orm.Model):

    _name = 'hr.contract.init.wage'
    _description = 'Starting Wages'

    _columns = {
        'job_id': fields.many2one(
            'hr.job',
            'Job',
        ),
        'starting_wage': fields.float(
            'Starting Wage',
            digits_compute=dp.get_precision('Payroll'),
            required=True
        ),
        'is_default': fields.boolean(
            'Use as Default',
            help="Use as default wage",
        ),
        'contract_init_id': fields.many2one(
            'hr.contract.init',
            'Contract Settings',
        ),
        'category_ids': fields.many2many(
            'hr.employee.category',
            'contract_init_category_rel',
            'contract_init_id',
            'category_id',
            'Tags',
        ),
    }

    def _rec_message(self, cr, uid, ids, context=None):
        return _('A Job Position cannot be referenced more than once in a '
                 'Contract Settings record.')

    _sql_constraints = [
        ('unique_job_cinit', 'UNIQUE(job_id,contract_init_id)', _rec_message),
    ]

    def unlink(self, cr, uid, ids, context=None):

        if isinstance(ids, (int, long)):
            ids = [ids]
        data = self.read(cr, uid, ids, ['contract_init_id'], context=context)
        for d in data:
            if not d.get('contract_init_id', False):
                continue
            d2 = self.pool.get(
                'hr.contract.init').read(cr, uid, d['contract_init_id'][0],
                                         ['state'], context=context)
            if d2['state'] in ['approve', 'decline']:
                raise orm.except_orm(
                    _('Error'),
                    _('You may not a delete a record that is not in a '
                      '"Draft" state')
                )
        return super(init_wage, self).unlink(cr, uid, ids, context=context)
