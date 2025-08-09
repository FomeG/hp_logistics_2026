from odoo import models, fields, api
from ...hp_components.services.department_service import DepartmentService

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
    assign_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assign User',
        default=lambda self: self.env.user
    )
    allow_assign_user_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_allow_assign_user_ids',
        store=False
    )
    _sql_constraints = [
        ('unique_tax', 'UNIQUE(tax_number)','Tax Number must be unique!'),
    ]

    @api.depends('name')
    def _compute_allow_assign_user_ids(self):
        service = DepartmentService(self.env)
        for rec in self:
            rec.allow_assign_user_ids = service.get_user_by_department_type('trucking')
