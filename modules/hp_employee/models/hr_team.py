from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrTeam(models.Model):
    _name = 'hr.team'
    _description = 'HR Team'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin','mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Team Name",
        required=True,
        tracking=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        tracking=True,
        default=lambda self: self.env.user.employee_id.department_id,
    )
    user_ids = fields.Many2many(
        'res.users',
        'hr_team_user_rel',
        'team_id', 'user_id',
        string="Members",
        tracking=True,
        # domain="[('id', 'in', available_user_ids)]"
    )

    allowed_department_ids = fields.Many2many(
        "hr.department", compute="_compute_allowed_department_ids", store=False
    )

    @api.depends_context("uid")
    def _compute_allowed_department_ids(self):
        user = self.env.user

        is_admin = user.has_group("base.group_system")

        managed_departments = self.env["hr.department"]
        if not (is_admin):
            managed_departments = self.env["hr.department"].search(
                [("manager_id.user_id", "=", user.id)]
            )

        for record in self:
            if is_admin:
                record.allowed_department_ids = self.env["hr.department"].search([])
            else:
                record.allowed_department_ids = managed_departments

    region_id = fields.Many2one(
        comodel_name='region',
        string="Region",
        tracking=True,
        ondelete='set null'
    )

    location_ids = fields.Many2many(
        'location.base',
        'hr_team_location_rel',
        'team_id', 'location_id',
        string="Ports",
        tracking=True
    )

    department_type_code = fields.Char(
        string="Department Type Code",
        related="department_id.department_type_id.code",
        store=False
    )

    is_department_required = fields.Boolean(compute="_compute_is_department_required")

    @api.depends_context("uid")
    def _compute_is_department_required(self):
        user = self.env.user
        user_service = self.env["hp_employee.user.service"]

        is_admin = user_service.is_admin_user(user.id)

        for record in self:
            record.is_department_required = not (is_admin)

    @api.constrains("department_id")
    def _check_department_required_constraint(self):
        for record in self:
            if record.is_department_required and not record.department_id:
                raise ValidationError("Department is required for this user.")
