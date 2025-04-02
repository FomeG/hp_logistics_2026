from odoo import api, fields, models, _
from datetime import date


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_type_filter = fields.Selection([
        ('pricing', "Pricing"),
        ('trucking', "Trucking"),
        ('common', "Common"),
        ('custom', "Custom"),
    ], string="Product Type", default='common')

    etd_sale = fields.Date(
        string="ETD Sale",
        help="Estimated Time of Departure for this Sale Order Line"
    )

    booking_id = fields.Many2one(
        'pricing.booking', string="Booking",
        domain="[('voyage_id.etd', '>=', etd_sale)]",
        tracking=True
    )

    volume_cont = fields.Selection([
        ('20DC', '20DC'),
        ('20RF', '20RF'),
        ('20OT', '20OT'),
        ('20HC', '20HC'),
        ('40DC', '40DC'),
        ('40HC', '40HC'),
        ('40HQ', '40HQ'),
        ('40RF', '40RF'),
        ('40HCRF', '40HCRF'),
        ('40OT', '40OT'),
    ], string="Container Type")

    @api.onchange('product_type_filter')
    def _onchange_product_type_filter(self):
        # Clear product when type filter changes
        if self.product_id and self.product_id.product_tmpl_id.type != self.product_type_filter:
            self.product_id = False
            self.product_template_id = False

    def action_create_pricing_sealine(self):
        """Open wizard to collect POD/POL information"""
        return {
            'name': _('Create POD/POL Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'pod.pol.request.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.onchange('product_type_filter')
    def _onchange_product_type_filter(self):
        if self.product_type_filter != 'pricing':
            self.etd_sale = False
            self.booking_id = False
            self.volume_cont = False