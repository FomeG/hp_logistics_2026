from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrLeaveInherit(models.Model):
    _inherit = 'hr.leave'

    request_refuse = fields.Boolean(string='Request Refuse', default=False)


    def action_request_refuse(self):
        self.sudo().write({
            'request_refuse': True,
        })
        return True