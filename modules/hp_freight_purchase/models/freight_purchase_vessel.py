from odoo import models, fields

class FreightPurchaseVessel(models.Model):
    _name = 'freight.purchase.vessel'
    _description = 'Vessel'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)

