from odoo import models, fields

class SaleOrderInherrit(models.Model):
    _inherit = 'sale.order'

    booking_ids = fields.Many2many(
        'pricing.booking',
        'sale_order_booking_rel',
        'sale_order_id',
        'booking_id',
        string="Bookings"
    )