from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class ShippingVessel(models.Model):
    _name = 'pricing.shipping.vessel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Shipping Vessel'
    _rec_name = 'vessel_name'
    _order = 'write_date desc'

    vessel_name = fields.Char(string='Tên tàu hàng', tracking=True)