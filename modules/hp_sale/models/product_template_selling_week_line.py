from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplateSellingWeekLine(models.Model):
    _name = 'product.template.selling.week.line'
    _description = 'Product Template Selling Week Line'

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
        'freight.purchase.region',
        string="Region",
        related='product_template_selling_week_id.product_template_id.region_id',
        store=False
    )
    selling_week_id = fields.Many2one(
        'selling.week',
        string="Selling Week",
        related='product_template_selling_week_id.selling_week_id',
        store=False
    )
    product_template_id = fields.Many2one(
        'product.template',
        string="Product",
        related='product_template_selling_week_id.product_template_id',
        store=False
    )

    name = fields.Char(string="name", compute='_compute_name', store=True)
    
    @api.depends('product_template_selling_week_id', 'shipping_line_id', 'container_type_id', 'price')
    def _compute_name(self):
        for record in self:
            product_template_name = record.product_template_selling_week_id.product_template_id.name
            shipping_line_name = record.shipping_line_id.name
            container_type_name = record.container_type_id.name
            price = record.price
            record.name = f"{product_template_name}: {container_type_name}/{price} ({shipping_line_name})"

    @api.model
    def action_add_selected_lines(self, selected_ids):
        sale_order_id = self.env.context.get('sale_order_id')
        lines = self.browse(selected_ids)
        if not sale_order_id or not lines:
            raise ValidationError("No Sale Order or selected lines found.")

        values = []
        for line in lines:
            product_template = line.product_template_selling_week_id.product_template_id
            values.append({
                'name': product_template.name,
                'order_id': sale_order_id,
                'product_id': product_template.product_variant_id.id,
                'container_type_id': line.container_type_id.id,
                'product_uom_qty': 1.0,
                'base_price': line.price,
                'price_unit': line.price,
                'product_type_filter': product_template.type,
            })

        self.env['sale.order.line'].sudo().create(values)
        return True