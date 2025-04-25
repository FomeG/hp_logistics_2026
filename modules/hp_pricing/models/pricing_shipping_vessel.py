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

    @api.constrains('vessel_name')
    def _check_unique_vessel_name(self):
        """ Ensure unique vessel_name """
        for record in self:
            existing_shipping_vessel = self.env['pricing.shipping.vessel'].search([
                ('vessel_name', 'ilike', record.vessel_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_shipping_vessel:
                raise ValidationError(_("The Shipping vessel name '%s' already exists.") % record.vessel_name)