from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class TruckingRoadline(models.Model):
    _name = 'trucking.roadline'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Trucking Roadline'
    _rec_name = 'roadline_name'
    _order = 'write_date desc'

    roadline_name = fields.Char(
        string='Roadline',
        compute='_compute_roadline',
        store=True,
    )
    pol_id = fields.Many2one(
        'trucking.pol', string='Place of Loading', tracking=True)
    pod_id = fields.Many2one(
        'trucking.pod', string='Place of Discharge', tracking=True)

    @api.depends('pol_id', 'pod_id')
    def _compute_roadline(self):
        for record in self:
            pol = record.pol_id.pol_name if record.pol_id else "Unknown Pol"
            pod = record.pod_id.pod_name if record.pol_id else "Unknown Pod"
            record.roadline_name = f"{pol} - {pod}"