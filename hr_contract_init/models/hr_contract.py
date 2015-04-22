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




class hr_contract(orm.Model):

    _inherit = 'hr.contract'

    def _get_wage(self, cr, uid, context=None, job_id=None):

        res = 0
        default = 0
        init = self.get_latest_initial_values(cr, uid, context=context)
        if job_id:
            catdata = self.pool.get('hr.job').read(
                cr, uid, job_id, ['category_ids'], context=context)
        else:
            catdata = False
        if init is not None:
            for line in init.wage_ids:
                if job_id is not None and line.job_id.id == job_id:
                    res = line.starting_wage
                elif catdata:
                    cat_id = False
                    category_ids = [c.id for c in line.category_ids]
                    for ci in catdata['category_ids']:
                        if ci in category_ids:
                            cat_id = ci
                            break
                    if cat_id:
                        res = line.starting_wage
                if line.is_default and default == 0:
                    default = line.starting_wage
                if res != 0:
                    break
        if res == 0:
            res = default
        return res

    def _get_struct(self, cr, uid, context=None):

        res = False
        init = self.get_latest_initial_values(cr, uid, context=context)
        if init is not None and init.struct_id:
            res = init.struct_id.id
        return res

    def _get_trial_date_start(self, cr, uid, context=None):

        res = False
        init = self.get_latest_initial_values(cr, uid, context=context)
        if init is not None and init.trial_period and init.trial_period > 0:
            res = datetime.now().strftime(OE_DFORMAT)
        return res

    def _get_trial_date_end(self, cr, uid, context=None):

        res = False
        init = self.get_latest_initial_values(cr, uid, context=context)
        if init is not None and init.trial_period and init.trial_period > 0:
            dEnd = datetime.now().date() + timedelta(days=init.trial_period)
            res = dEnd.strftime(OE_DFORMAT)
        return res

    _defaults = {
        'wage': _get_wage,
        'struct_id': _get_struct,
        'trial_date_start': _get_trial_date_start,
        'trial_date_end': _get_trial_date_end,
    }

    def onchange_job(self, cr, uid, ids, job_id, context=None):

        res = False
        if job_id:
            wage = self._get_wage(cr, uid, context=context, job_id=job_id)
            res = {'value': {'wage': wage}}
        return res

    def onchange_trial(self, cr, uid, ids, trial_date_start, context=None):

        res = {'value': {'trial_date_end': False}}

        init = self.get_latest_initial_values(cr, uid, context=context)
        if init is not None and init.trial_period and init.trial_period > 0:
            dStart = datetime.strptime(trial_date_start, OE_DFORMAT)
            dEnd = dStart + timedelta(days=init.trial_period)
            res['value']['trial_date_end'] = dEnd.strftime(OE_DFORMAT)

        return res

    def get_latest_initial_values(self, cr, uid, today_str=None, context=None):
        """Return a record with an effective date before today_str
        but greater than all others
        """

        init_obj = self.pool.get('hr.contract.init')
        if today_str is None:
            today_str = datetime.now().strftime(OE_DFORMAT)
        dToday = datetime.strptime(today_str, OE_DFORMAT).date()

        res = None
        ids = init_obj.search(
            cr, uid, [('date', '<=', today_str), ('state', '=', 'approve')],
            context=context)
        for init in init_obj.browse(cr, uid, ids, context=context):
            d = datetime.strptime(init.date, OE_DFORMAT).date()
            if d <= dToday:
                if res is None:
                    res = init
                elif d > datetime.strptime(res.date, OE_DFORMAT).date():
                    res = init

        return res
