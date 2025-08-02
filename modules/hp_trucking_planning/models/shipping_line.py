from odoo import models, fields


class ShippingLine(models.Model):
    _name = 'trucking_planning.shipping_line'
    _description = 'Shipping Line'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin']
    name = fields.Char(
        string='Name',
        required=True,
    )