from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PricingSealine(models.Model):
    _name = 'pricing.sealine'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Sealine'
    _rec_name = 'sealine_name'
    _order = 'write_date desc'

    sealine_name = fields.Char(
        string='Sealine',
        compute='_compute_sealine',
        store=True,
    )
    pol_id = fields.Many2one(
        'pricing.pol', string='Port of Loading', tracking=True)
    pod_id = fields.Many2one(
        'pricing.pod', string='Port of Discharge', tracking=True)

    @api.depends('pol_id', 'pod_id')
    def _compute_sealine(self):
        for record in self:
            pol = record.pol_id.pol_name if record.pol_id else "Unknown Pol"
            pod = record.pod_id.pod_name if record.pol_id else "Unknown Pod"
            record.sealine_name = f"{pol} - {pod}"

    @api.constrains('sealine_name')
    def _check_unique_sealine_name(self):
        """ Ensure unique sealine_name """
        for record in self:
            existing_sealine = self.env['pricing.sealine'].search([
                ('sealine_name', 'ilike', record.sealine_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_sealine:
                raise ValidationError(_("The sealine name '%s' already exists.") % record.sealine_name)