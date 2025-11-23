from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplateSellingWeek(models.Model):
    _name = 'product.template.selling.week'
    _description = 'Product Template Selling Week'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
        required=True,
        tracking=True,
        domain="[('id', 'in', available_product_template_ids)]"
    )
    team_id = fields.Many2one(
        'hr.team',
        string="Team",
        tracking=True
    )
    region_id = fields.Many2one(
        comodel_name='region',
        string="Region",
        related='product_template_id.region_id'
    )
    line_ids = fields.One2many(
        'product.template.selling.week.line',
        'product_template_selling_week_id',
        tracking=True,
        copy=True
    )
    note = fields.Char()

    name = fields.Text(string="Name", compute="_compute_name", store=True)
    available_product_template_ids = fields.Many2many('product.template', compute='_compute_available_product_template_ids', store=False)

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
    
    @api.depends('team_id')
    def _compute_available_product_template_ids(self):
        ProductTemplate = self.env['product.template']
        for record in self:
            locations = self.team_id.location_ids
            if not locations:
                record.available_product_template_ids = []
            else:
                routes = self.env['route.base'].search([('to_location_id', 'in', locations.ids)])
                record.available_product_template_ids =  ProductTemplate.search([('route_id', 'in', routes.ids)])