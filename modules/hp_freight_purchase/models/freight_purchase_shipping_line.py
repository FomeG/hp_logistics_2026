from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class FreightShippingLine(models.Model):
    _name = 'freight.purchase.shipping.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Shipping Line'
    _rec_name = 'line_name'
    _order = 'write_date desc'

    line_name = fields.Char(string='Shipping Line Name', tracking=True)
    line_email = fields.Char(string='Shipping Line Email', tracking=True)

    @api.constrains('line_name')
    def _check_unique_line_name(self):
        """ Ensure unique line_name """
        for record in self:
            existing_shipping_line = self.env['freight.purchase..shipping.line'].search([
                ('line_name', 'ilike', record.line_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_shipping_line:
                raise ValidationError(_("The Shipping line name '%s' already exists.") % record.line_name)