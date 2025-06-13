from odoo import models, fields

class FreightPurchaseQuotationLine(models.Model):
    _name = 'freight.purchase.quotation.line'
    _description = 'Purchase Quotation Line'

    quotation_id = fields.Many2one('freight.purchase.quotation', required=True, ondelete='cascade')
    container_type_id = fields.Many2one('container.type', required=True)
    cost = fields.Float(string="booking price",required=True)
    price = fields.Float(string="internal price set by sale director",default=lambda self: self.cost if self.cost else 0.0)
