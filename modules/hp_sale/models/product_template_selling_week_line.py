from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplateSellingWeekLine(models.Model):
    _name = 'product.template.selling.week.line'
    _description = 'Weekly Sea Freight Of Each Shipping Line For Sale Team'

    product_template_selling_week_id = fields.Many2one(
        'product.template.selling.week',
        string="Product Selling Week",
        required=True,
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        required=True,
    )
    container_type_id = fields.Many2one(
        'container.type',
        string="Container Type",
        required=True,
        domain=[('is_active', '=', True)],
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )
    price = fields.Monetary(
        string="Price",
        currency_field='currency_id'
    )
    product_tag_ids = fields.Many2many(
        string="Fee",
        comodel_name='product.tag'
    )

    region_id = fields.Many2one(
        comodel_name='region',
        string="Region",
        related='product_template_selling_week_id.region_id',
        store=False
    )
    selling_week_id = fields.Many2one(
        'selling.week',
        string="Selling Week",
        related='product_template_selling_week_id.selling_week_id',
        store=False
    )
    from_location_id = fields.Many2one(
        comodel_name='location.base',
        string="POL",
        related='product_template_selling_week_id.from_location_id',
        store=False
    )
    to_location_id = fields.Many2one(
        comodel_name='location.base',
        string="POD",
        related='product_template_selling_week_id.to_location_id',
        store=False
    )
    name = fields.Char(string="name", compute='_compute_name', store=True)
    
    @api.depends('product_template_selling_week_id', 'shipping_line_id', 'container_type_id', 'price')
    def _compute_name(self):
        for record in self:
            name = f"{record.from_location_id.name} - {record.to_location_id.name}"
            shipping_line_name = record.shipping_line_id.name
            container_type_name = record.container_type_id.name
            price = record.price
            record.name = f"{name}: {container_type_name}/{price} ({shipping_line_name})"

    def action_add_selected_lines(self):
        sale_order_id = self.env.context.get('sale_order_id')
        lines = self
        if not sale_order_id or not lines:
            raise ValidationError("No Sale Order or selected lines found.")

        so = self.env['sale.order'].browse(sale_order_id)
        product_id = self.env.ref('hp_sale.product_truck_freight').id
        values = []
        for line in lines:
            price_in_so_currency = so._convert_to_order_currency(line.price, line.currency_id)

            values.append({
                'name': f"{line.from_location_id.name} - {line.to_location_id.name}",
                'order_id': sale_order_id,
                'product_id': product_id,
                'container_type_id': line.container_type_id.id,
                'product_uom_qty': 1.0,
                'currency_id_line': line.currency_id.id,
                'price_unit_original': line.price,
                'price_unit': price_in_so_currency,
            })

        self.env['sale.order.line'].sudo().create(values)
        return True