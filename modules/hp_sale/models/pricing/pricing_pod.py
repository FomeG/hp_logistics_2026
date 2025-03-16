from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PortOfDischarge(models.Model):
    _name = 'pricing.pod'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Port Of Discharge'
    _rec_name = 'pod_name'
    _order = 'write_date desc'

    pod_name = fields.Char(string='Cảng dỡ hàng', tracking=True)
    region_id = fields.Many2one(
        'pricing.region', string='Khu vực vận chuyển', tracking=True)