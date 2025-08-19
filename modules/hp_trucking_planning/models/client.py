from odoo import models, fields, api
from ...hp_components.services.department_service import DepartmentService

class Client(models.Model):
    _name = 'trucking_planning.client'
    _description = 'Client'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

    code = fields.Char(
        string= 'Client Code',
        required=True,
        tracing=True
    )
    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
    )
    phone = fields.Char(
        string="Phone",
        tracking=True,
    )
    address = fields.Char(
        string="Address",
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
        default=lambda self: self.env.user,
        domain=lambda self: self._get_assign_user_domain(),
    )
    branch_id = fields.Many2one(
        comodel_name='trucking_planning.branch',
        index=True,
        string='Branch',
        tracking=True,
    )
    _sql_constraints = [
        ('unique_tax', 'UNIQUE(tax_number)','Tax Number must be unique!'),
    ]

    @api.model
    def _get_assign_user_domain(self):
        allow_assign_users = DepartmentService(self.env).get_user_by_department_type(DepartmentService.DEPARTMENT_TYPE_TRUCKING)

        return [
            ('id', 'in', allow_assign_users.ids),
        ]