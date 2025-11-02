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
    note = fields.Char(string="Note")
