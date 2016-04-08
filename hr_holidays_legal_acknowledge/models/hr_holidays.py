# -*- coding: utf-8 -*-
# ©  2016 AMETRAS Documents (http://www.ametras.doc)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.exceptions import Warning as UserError


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    legal_acknowledge = fields.Boolean('Legal Acknowledge Check')
    
    @api.multi
    def write(self, vals):
        holiday = super(HrHolidays, self).write(vals)
        status_id = vals.get('holiday_status_id', False) or self.holiday_status_id.id
        check = vals.get('legal_acknowledge', False) or self.legal_acknowledge
        status = self.env['hr.holidays.status'].browse(status_id)            
        if 'Legal' in status.name and self.type == 'remove':
            if not check:
                raise UserError('You cannot save a legal leave without '
                                'checking the Legal Acknowledge Check Box.')
        return holiday

    @api.model
    def create(self, vals):
        holiday = super(HrHolidays, self).create(vals)    
        status_id = vals.get('holiday_status_id', False) or self.holiday_status_id.id
        check = vals.get('legal_acknowledge', False) or self.legal_acknowledge
        status = self.env['hr.holidays.status'].browse(status_id)            
        if 'Legal' in status.name and self.type == 'remove':
            if not check:
                raise UserError('You cannot save a legal leave without '
                                'checking the Legal Acknowledge Check Box.')
        return holiday
