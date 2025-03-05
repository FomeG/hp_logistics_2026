from odoo import api, fields, models, tools, _

class ProductCategory(models.Model):
    _inherit = "product.category"

    allowed_type_id = fields.Selection(
        selection=[
            ('common', "Common"),
            ('custom', "Custom"),
        ],
        string="Allowed Product Type",
        required=True,
        help="Only products of this type can belong to this category."
    )
