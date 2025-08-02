from odoo import models, fields


class PartnerMainType(models.Model):
    _name = 'partner.main.type'
    _description = 'Partner Main Type'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin']

    name = fields.Char(required=True)