from odoo import models, fields


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking id',
        index=True,
    )
    booking_code = fields.Char(
        string='Booking Code',
        related='booking_id.code',
        readonly=True,
        store=False,
    )