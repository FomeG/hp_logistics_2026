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
        comodel_name='region',
        string="Region",
        tracking=True
    )

    @api.model
    def action_sale_order_add_selected_lines(self, selected_ids):
        sale_order_id = self.env.context.get('sale_order_id')
        lines = self.browse(selected_ids)
        if not sale_order_id or not lines:
            raise ValidationError("No Sale Order or selected lines found.")

        values = []
        for line in lines:
            values.append({
                'name': line.name,
                'order_id': sale_order_id,
                'product_id': line.product_variant_id.id,
                'product_uom_qty': 1.0,
                'base_price': line.list_price,
                'price_unit': line.list_price,
                'product_type_filter': line.type,
            })

        self.env['sale.order.line'].sudo().create(values)
        return True
