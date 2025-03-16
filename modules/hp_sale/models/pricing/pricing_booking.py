from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PricingBooking(models.Model):
    _name = 'pricing.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Region'
    _rec_name = 'booking_no'
    _order = 'write_date desc'

    booking_no = fields.Char(string='Số booking', tracking=True)
    voyage_id = fields.Many2one(
        'pricing.voyage', string="Tàu và số hiệu chuyến",
        tracking=True
    )
    volume = fields.Char(string='Khối lượng vận chuyển', tracking=True)
    booking_price = fields.Float('Giá book', tracking=True)
    booking_status = fields.Selection(selection=[
        ('booked', 'Booked'),
        ('request', 'Request'),
        ('cancel', 'Cancel'),
        ('available', 'Available'),
    ], string='Booking Status', default='available', tracking=True)

