from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    type = fields.Selection(selection=[
            ('pricing', "Pricing"),
            ('trucking', "Trucking"),
            ('common', "Common"),
            ('custom', "Custom"),
        ], required=True, default='common')
    
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

    region_id = fields.Many2one(
        'freight.purchase.region',
        string="Region",
        tracking=True
    )
