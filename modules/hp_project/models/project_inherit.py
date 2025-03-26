from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectInherit(models.Model):
    _inherit = 'project.project'

    REQUEST_PRICE = 'request_price'
    REQUEST_PRODUCT = 'request_product'
    ASSIGN_BOOKING = 'assign_booking'
    APPROVE_QUOTATION = 'approve_quotation'

    PROTECTED_TYPE = {REQUEST_PRICE, REQUEST_PRODUCT, ASSIGN_BOOKING, APPROVE_QUOTATION}

    type = fields.Char(string="Type")

    def unlink(self):
        for record in self:
            if record.type in self.PROTECTED_TYPE:
                raise UserError(_("You cannot delete this this project."))
        return super().unlink()
    