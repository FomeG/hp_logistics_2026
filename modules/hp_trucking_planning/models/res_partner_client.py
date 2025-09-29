from odoo import models, fields, api
from ...hp_components.services.department_service import DepartmentService

class ResPartnerClient(models.Model):
    _inherit = ['res.partner.client']

    route_ids = fields.Many2many(
        comodel_name='trucking_planning.route',
        string='Routes',
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        inverse_name='client_id',
        string='Trips'
    )
    assign_trucking_manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Assign User',
        default=lambda self: self.env.user,
        domain=lambda self: self._get_assign_user_domain(),
        tracking=True,
    )
    trucking_branch_id = fields.Many2one(
        comodel_name='trucking_planning.branch',
        index=True,
        string='Branch',
        default=lambda self: self.env.user.branch_ids[:1].id,
    )

    # compute field
    can_edit_assign_user = fields.Boolean(compute="_compute_can_edit_assign_user", store=False)


    @api.model
    def _get_assign_user_domain(self):
        allow_assign_users = DepartmentService(self.env).get_user_by_department_type(DepartmentService.DEPARTMENT_TYPE_TRUCKING)

        return [
            ('id', 'in', allow_assign_users.ids),
        ]

    @api.depends()
    def _compute_can_edit_assign_user(self):
        for record in self:
            record.can_edit_assign_user = self.env.user.has_group('hp_trucking_planning.group_hp_trucking_planning_lead')