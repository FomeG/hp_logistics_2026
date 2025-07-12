from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrderLineInherit(models.Model):
    _inherit = ['sale.order.line']
    _name = 'sale.order.line'

    container_type_id = fields.Many2one('container.type', string='Container Type')
    booking_id = fields.Many2one('freight.purchase.booking', string="Pricing Booking", tracking=True)
    etd_sale = fields.Date(string="ETD Sale", help="Estimated Time of Departure for this Sale Order Line")
    base_price = fields.Float(string="Base Price", default=0.0)
    commission = fields.Float(string="Commission (%)", default=0.0)
    quotation_id = fields.Many2one('freight.purchase.quotation',
        string="Pricing Quotation",
        tracking=True
    )
    product_type_filter = fields.Selection([
        ('pricing', "Pricing"),
        ('trucking', "Trucking"),
        ('common', "Common"),
        ('custom', "Custom"),
    ], string="Product Type (Filter)", default='common')
