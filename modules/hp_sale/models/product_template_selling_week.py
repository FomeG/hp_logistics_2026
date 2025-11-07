from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplateSellingWeek(models.Model):
    _name = 'product.template.selling.week'
    _description = 'Product Template Selling Week'

    goods_info = fields.Char(
        string="Goods Info",
        required=True,
        tracking=True
    )
    selling_week_id = fields.Many2one(
        'selling.week',
        string="Selling Week",
        tracking=True
    )
    product_template_id = fields.Many2one(
        'product.template',
        string="Product",
        tracking=True
    )
    team_id = fields.Many2one(
        'hr.team',
        string="Team",
        tracking=True
    )
    region_id = fields.Many2one(
        'freight.purchase.region',
        string="Region",
        related='product_template_id.region_id'
    )
    line_ids = fields.One2many(
        'product.template.selling.week.line',
        'product_template_selling_week_id',
        tracking=True
    )
    note = fields.Char()

    name = fields.Text(string="Name", compute="_compute_name", store=True)

    @api.depends('goods_info', 'product_template_id', 'line_ids')
    def _compute_name(self):
        for record in self:
            goods_part = record.goods_info or ''
            product_part = record.product_template_id.name or ''

            line_parts = []
            for line in record.line_ids:
                container = line.container_type_id.name or ''
                price = str(line.price or '')
                fees =  line.product_tag_ids.mapped('name')
                fee_string = ', '.join(fees) if fees else ''
                ship = line.shipping_line_id.name or ''
                line_parts.append(f"{container}/{price} {fee_string} ({ship})")

            lines_text = ', '.join(line_parts) if line_parts else ''

            if goods_part or product_part or lines_text:
                record.name = f"{goods_part}\n{product_part}: {lines_text}"
            else:
                record.name = ''