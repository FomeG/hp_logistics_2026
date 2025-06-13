from odoo import models, fields

class FreightPurchaseQuotation(models.Model):
    _name = 'freight.purchase.quotation'
    _description = 'Freight Purchase Quotation'
    _inherit = ['unique.code.mixin']
    name = fields.Char(required=True, string='Quotation Name')
    route_id = fields.Many2one('freight.purchase.route', required=True)
    shipping_line_id = fields.Many2one('res.partner', domain="[('is_shipping_line', '=', True)]", required=True)

    available_from = fields.Date(required=True)
    available_to = fields.Date(required=True)
    fees = fields.Many2many('freight.purchase.fee', string='Fees')
    note = fields.Text()
    is_active = fields.Boolean(default=True)
    line_ids = fields.One2many('freight.purchase.quotation.line', 'quotation_id')


