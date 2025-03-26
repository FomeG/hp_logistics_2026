from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PricingRegion(models.Model):
    _name = 'pricing.region'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Region'
    _rec_name = 'region_name'
    _order = 'write_date desc'

    region_name = fields.Char(string='Region', tracking=True)
    member_ids = fields.One2many(
        'res.users', 'region_id', string='Pricing Member',
        domain="[('share', '=', False), ('region_id', '=', False)]",
        tracking=True)
