from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class ShippingLine(models.Model):
    _name = 'pricing.shipping.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Shipping Line'
    _rec_name = 'line_name'
    _order = 'write_date desc'

    line_name = fields.Char(string='Tên hãng tàu', tracking=True)
    line_email = fields.Char(string='Email hãng tàu', tracking=True)