from odoo import models, fields

class FreightPurchaseQuotation(models.Model):
    _name = 'freight.purchase.quotation'
    _description = 'Freight Purchase Quotation'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string='Quotation Name', tracking=True)
    route_id = fields.Many2one('freight.purchase.route', required=True, tracking=True)
    shipping_line_id = fields.Many2one('res.partner', domain="[('is_shipping_line', '=', True)]", required=True, tracking=True)

    available_from = fields.Date(required=True, tracking=True)
    available_to = fields.Date(required=True, tracking=True)
    fees = fields.Many2many('freight.purchase.fee', string='Fees', tracking=True)
    note = fields.Text()
    is_active = fields.Boolean(default=True, tracking=True)
    line_ids = fields.One2many('freight.purchase.quotation.line', 'quotation_id', tracking=True)


