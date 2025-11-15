from odoo import models, fields

class ContainerType(models.Model):
    _name = 'container.type'
    _description = 'Container Type'
    _inherit = ['unique.code.mixin','unique.normalized.name.mixin','mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    teu = fields.Float(required=True,  default=20.0, tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)