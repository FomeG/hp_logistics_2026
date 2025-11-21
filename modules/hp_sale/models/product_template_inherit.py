from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models import constants

class ProductTemplate(models.Model):
    _inherit = "product.template"

    route_id = fields.Many2one(
        'route.base',
        string='Route',
        tracking=True
    )
    type = fields.Selection(
        constants.ProductTemplateType.SELECT_OPTIONS,
        required=True,
        default=constants.ProductTemplateType.SEA_FREIGHT
    )

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

    @api.model
    def get_or_create_from_route_base(self, route_base):
        product = self.search([('route_id', '=', route_base.id)], limit=1)
        if not product:
            type = constants.ProductTemplateType.SEA_FREIGHT
            if route_base.is_for_truck_freight:
                type = constants.ProductTemplateType.TRUCK_FREIGHT
            self.create({
                'name': route_base.name,
                'route_id': route_base.id,
                'type': type,
                'categ_id': self.env.ref('hp_sale.product_category_sea_freight').id,
                'list_price': route_base.total_cost,
                'standard_price': route_base.total_cost,
            })
        return product