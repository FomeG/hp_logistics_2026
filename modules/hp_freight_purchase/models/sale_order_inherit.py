from odoo import models, fields


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    freight_booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking',
        readonly=True,
    )