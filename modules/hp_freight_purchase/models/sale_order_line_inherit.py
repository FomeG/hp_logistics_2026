from odoo import models, fields


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    _order = 'create_date desc'

    booking_line_id = fields.Many2one('freight.purchase.booking.line')