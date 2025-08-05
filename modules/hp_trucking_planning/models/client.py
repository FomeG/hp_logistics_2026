from odoo import models, fields


class Client(models.Model):
    _name = 'trucking_planning.client'
    _description = 'Client'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
    )
    phone = fields.Char(
        string="Phone",
        tracking=True,
    )
    tax_number = fields.Char(
        string='Tax Number',
        required=True,
        tracking=True,
    )
    route_ids = fields.Many2many(
        comodel_name='trucking_planning.route',
        string='Routes',
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        inverse_name='client_id',
        string='Trips'
    )
    _sql_constraints = [
        ('unique_tax', 'UNIQUE(tax_number)','Tax Number must be unique!'),
    ]

