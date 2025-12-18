from odoo import models, fields, api

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env['res.currency'].get_base_currency(),
        required=True
    )

