from odoo import models, fields


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    _order = 'create_date desc'

    booking_line_id = fields.Many2one('freight.purchase.booking.line')

    def action_select_this_line(self):
        booking_line_id = self.env.context.get('booking_line_id')
        if booking_line_id:
            self.write({'booking_line_id': booking_line_id})
        return {'type': 'ir.actions.act_window_close'}