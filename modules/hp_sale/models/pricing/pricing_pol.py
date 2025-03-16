from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PortOfLoading(models.Model):
    _name = 'pricing.pol'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Port Of Loading'
    _rec_name = 'pol_name'
    _order = 'write_date desc'

    pol_name = fields.Char(string='Cảng xếp hàng', tracking=True)