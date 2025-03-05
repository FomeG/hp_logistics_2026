from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

# First, extend product.category to add the allowed types
class ProductCategory(models.Model):
    _inherit = "product.category"
    
    allowed_type_ids = fields.Many2one(
        'ir.model.fields.selection',
        domain="[('model', '=', 'product.template'), ('name', '=', 'type')]",
        string="Allowed Product Types",
        help="Product types that can be assigned to this category"
    )
