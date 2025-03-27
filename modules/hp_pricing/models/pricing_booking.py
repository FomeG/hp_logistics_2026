from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PricingBooking(models.Model):
    _name = 'pricing.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Booking'
    _rec_name = 'booking_no'
    _order = 'write_date desc'

    booking_no = fields.Char(string='Booking No', tracking=True)
    voyage_id = fields.Many2one(
        'pricing.voyage', string="Tàu và số hiệu chuyến",
        tracking=True
    )
    volume_quantity_1 = fields.Integer(string='Container Quantity 1', default=1, tracking=True)
    volume_cont_1 = fields.Selection(selection=[
        ('20DC', '20DC'),
        ('20RF', '20RF'),
        ('20OT', '20OT'),
        ('20HC', '20HC'),
        ('40DC', '40DC'),
        ('40HC', '40HC'),
        ('40HQ', '40HQ'),
        ('40RF', '40RF'),
        ('40HCRF', '40HCRF'),
        ('40OT', '40OT'),
    ], string='Container Type 1', default='40HC', tracking=True)
    volume_quantity_2 = fields.Integer(string='Container Quantity 2', default=0, tracking=True)
    volume_cont_2 = fields.Selection(selection=[
        ('20DC', '20DC'),
        ('20RF', '20RF'),
        ('20OT', '20OT'),
        ('20HC', '20HC'),
        ('40DC', '40DC'),
        ('40HC', '40HC'),
        ('40HQ', '40HQ'),
        ('40RF', '40RF'),
        ('40HCRF', '40HCRF'),
        ('40OT', '40OT'),
    ], string='Container Type 2', default='40HC', tracking=True)
    volume_total = fields.Integer(string='Total Volume (TEU)', compute='_compute_volume_total', store=True)
    booking_price = fields.Float('Booking Price', tracking=True)
    company_booking_price = fields.Float('Company Booking Price', tracking=True)
    booking_status = fields.Selection(selection=[
        ('booked', 'Booked'),
        ('request', 'Request'),
        ('cancel', 'Cancel'),
        ('available', 'Available'),
    ], string='Booking Status', default='available', tracking=True)

    active = fields.Boolean(default=True)

    @api.depends('volume_quantity_1', 'volume_cont_1', 'volume_quantity_2', 'volume_cont_2')
    def _compute_volume_total(self):
        for record in self:
            total_teu = 0

            # Calculation for first container
            if record.volume_quantity_1 > 0:
                if record.volume_cont_1 in ['20DC', '20RF', '20OT', '20HC']:
                    total_teu += record.volume_quantity_1 * 1
                elif record.volume_cont_1 in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    total_teu += record.volume_quantity_1 * 2

            # Calculation for second container
            if record.volume_quantity_2 > 0:
                if record.volume_cont_2 in ['20DC', '20RF', '20OT', '20HC']:
                    total_teu += record.volume_quantity_2 * 1
                elif record.volume_cont_2 in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    total_teu += record.volume_quantity_2 * 2

            record.volume_total = total_teu

