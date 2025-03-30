from odoo import api, fields, models
from datetime import date


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_type_filter = fields.Selection([
        ('pricing', "Pricing"),
        ('trucking', "Trucking"),
        ('common', "Common"),
        ('custom', "Custom"),
    ], string="Product Type", default='common')

    booking_id = fields.Many2one(
        'pricing.booking', string="Booking",
        domain="[('voyage_id.etd', '>', '{}')]".format(date.today()),
        tracking=True
    )

    @api.onchange('product_type_filter')
    def _onchange_product_type_filter(self):
        # Clear product when type filter changes
        if self.product_id and self.product_id.product_tmpl_id.type != self.product_type_filter:
            self.product_id = False
            self.product_template_id = False