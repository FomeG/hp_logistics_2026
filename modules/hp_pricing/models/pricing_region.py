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

    @api.constrains('region_name')
    def _check_unique_region_name(self):
        """ Ensure unique region_name """
        for record in self:
            existing_region = self.env['pricing.region'].search([
                ('region_name', 'ilike', record.region_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_region:
                raise ValidationError(_("The region name '%s' already exists.") % record.region_name)
