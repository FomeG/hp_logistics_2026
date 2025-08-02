from odoo import models, fields


class Client(models.Model):
    _name = 'trucking_planning.client'
    _description = 'Client'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin']

    name = fields.Char(
        required=True
    )
    phone = fields.Char(
    )
    tax_number = fields.Char(
        string='Tax Number',
        required=True,
    )
    route_ids = fields.Many2many(
        comodel_name='trucking_planning.route',
        string='Routes'
    )
    plan_ids = fields.One2many(
        comodel_name='trucking_planning.plan',
        inverse_name='client_id',
    )
    _sql_constraints = [
        ('unique_tax', 'UNIQUE(tax_number)','Tax Number must be unique!'),
    ]

