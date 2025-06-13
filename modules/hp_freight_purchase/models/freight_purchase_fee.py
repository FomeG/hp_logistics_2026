from odoo import models, fields

class FreightPurchaseFee(models.Model):
    _name = 'freight.purchase.fee'
    _description = 'Additional Fee from Shipping Line'
    _inherit = ['unique.code.mixin']
    name = fields.Char(required=True)
    amount = fields.Float(required=False)

