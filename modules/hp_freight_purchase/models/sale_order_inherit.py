from odoo import models, fields


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    booking_line_id = fields.Many2one(
        comodel_name= 'freight.purchase.booking.line',
        string='Booking Line id',
        index=True,
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        related='booking_line_id.booking_id',
        readonly=True,
        index=True,
        store=False,
    )
    booking_code = fields.Char(
        string='Booking Code',
        related='booking_id.code',
        readonly=True,
        store=False,
    )