from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"


    def action_sale_order_add_selected_lines(self):
        sale_order_id = self.env.context.get('sale_order_id')
        is_truck_freight = self.env.context.get('is_truck_freight')
        lines = self
        if not sale_order_id or not lines:
            raise ValidationError("No Sale Order or selected lines found.")
        
        values = []
        for line in lines:
            price = line.route_id.total_cost if is_truck_freight else line.list_price
            values.append({
                'name': line.name,
                'order_id': sale_order_id,
                'product_id': line.product_variant_id.id,
                'product_uom_qty': 1.0,
                'price_unit': price,
            })

        self.env['sale.order.line'].sudo().create(values)
        return True
