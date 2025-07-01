from odoo import models, fields


class FreightPurchaseFeeType(models.Model):
    _name = 'freight.purchase.fee.type'
    _description = 'Freight Purchase Fee Type'
    _inherit = ['unique.normalized.name.mixin']
    name = fields.Char(string='Fee Type', required=True)
    active = fields.Boolean(default=True, required=True)