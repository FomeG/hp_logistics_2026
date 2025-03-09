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

    region_name = fields.Char(string='Khu vực vận chuyển', tracking=True)
