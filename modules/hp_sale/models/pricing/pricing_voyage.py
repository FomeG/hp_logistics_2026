from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PricingVoyage(models.Model):
    _name = 'pricing.voyage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Voyage'
    _rec_name = 'display_name'
    _order = 'write_date desc'

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )

    shipping_vessel_id = fields.Many2one(
        'pricing.shipping.vessel', string="Tàu hàng",
        tracking=True
    )
    voyage_no = fields.Char(string='Số hiệu chuyến tàu', tracking=True)
    shipping_line_id = fields.Many2one(
        'pricing.shipping.line', string="Hãng tàu",
        tracking=True
    )
    etd = fields.Date(
        string="Ngày khởi hành",
        help="Ngày khởi hành"
    )
    pricing_member_id = fields.Many2one(
        'pricing.team.member', string="Nhân viên Pricing",
        tracking=True
    )
    pol_id = fields.Many2one(
        'pricing.pol', string="Cảng xếp hàng",
        tracking=True
    )
    pod_id = fields.Many2one(
        'pricing.pod', string="Cảng dỡ hàng",
        tracking=True
    )

    # display_name
    @api.depends('shipping_vessel_id.vessel_name', 'voyage_no')
    def _compute_display_name(self):
        for record in self:
            vessel = record.shipping_vessel_id.vessel_name if record.shipping_vessel_id else "Unknown Vessel"
            voyage = record.voyage_no if record.voyage_no else "Unknown Voyage"
            record.display_name = f"{vessel} {voyage}"
