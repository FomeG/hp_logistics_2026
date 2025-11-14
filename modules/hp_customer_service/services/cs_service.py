from datetime import date

from odoo import models


class CsService(models.AbstractModel):
    _name = 'cs.service'

    def generate_code_from_sale_order(self, sale_order, sequence_code):

        today = date.today()
        name = 'CS'
        if sale_order.branch_id:
            name = sale_order.branch_id.code
        else:
            partner = self.env.user.partner_id
            if partner and partner.branch_id:
                name = partner.branch_id.code

        return  f"{name}{today.strftime('%Y%m%d')}{self.env['ir.sequence'].next_by_code(sequence_code)}"