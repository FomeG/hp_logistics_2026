from odoo import models, fields

class FreightPurchaseFee(models.Model):
    _name = 'freight.purchase.fee'
    _description = 'Additional Fee from Shipping Line'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    amount = fields.Float(required=False, tracking=True)

