from odoo import models, fields

class FreightPurchaseVessel(models.Model):
    _name = 'freight.purchase.vessel'
    _description = 'Vessel'
    _inherit = ['unique.code.mixin']
    name = fields.Char(required=True)
    is_active = fields.Boolean(string='Is Active', default=True)

