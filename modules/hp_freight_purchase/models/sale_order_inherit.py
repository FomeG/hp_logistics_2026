from odoo import models, fields


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    freight_booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking',
        readonly=True,
    )

    direction = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('N/A', 'N/A'),
    ], string="Direction", required=True, tracking=True)

    etd_sale = fields.Date(string="ETD Sale", help="Estimated Time of Departure for this Sale Order Line")
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]"
    )