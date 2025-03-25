from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Add new product types while removing Odoo's default types
    def _selection_type(self):
        """ Remove Odoo's default types and only keep the custom ones. """
        return [
            ('pricing', "Pricing"),
            ('trucking', "Trucking"),
            ('common', "Common"),
            ('custom', "Custom"),
        ]

    type = fields.Selection(selection=_selection_type, required=True, default='common')
    
    complete_time = fields.Float(
        string="Thời gian hoàn thành (s)",
        digits=(3, 1),
        help="Thời gian hoàn thành dịch vụ"
    )
    
    # Add field for tiered pricing
    tiered_price = fields.Float(
        string="Giá lũy tiến",
        digits='Product Price',
        help="Giá từ sp thứ 2"
    )
    
    price_type = fields.Selection([
        ('common', 'Common Price'),
        ('tiered', 'Tiered Pricing'),
    ], string='Price Type', default='common')

