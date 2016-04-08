# -*- coding: utf-8 -*-
# ©  2016 AMETRAS Documents (http://www.ametras.doc)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def onchange_date_to(self, date_to, date_from):
        res = super(HrHolidays, self).onchange_date_to(date_to, date_from)
        res['value']['date_from'] = fields.Datetime.to_string(
            fields.Date.from_string(date_from))
        return res
