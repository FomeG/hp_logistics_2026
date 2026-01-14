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
        default=lambda self: [(6, 0, [self.env.uid])],
        # domain="[('id', 'in', available_user_ids)]"
    )

    allowed_department_ids = fields.Many2many(
        "hr.department", compute="_compute_allowed_department_ids", store=False
    )

    @api.depends()
    def _compute_allowed_department_ids(self):
        allowed_departments = self._get_allowed_department_ids()
        for record in self:
            record.allowed_department_ids = allowed_departments


    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'allowed_department_ids' in fields_list:
            defaults['allowed_department_ids'] = [(6, 0, self._get_allowed_department_ids().ids)]
        return defaults

    @api.model
    def _get_allowed_department_ids(self):
        """Get allowed departments for current user, optionally filtered by department type from context."""
        user = self.env.user
        is_admin = user.has_group("base.group_system")

        if is_admin:
            departments = self.env["hr.department"].search([])
        else:
            departments = self.env["hr.department"].search(
                [("manager_id.user_id", "=", user.id)]
            )

        # Filter by department type if specified in context
        dept_type_code = self.env.context.get('default_department_type_code')
        if dept_type_code:
            departments = departments.filtered(
                lambda d: d.department_type_id.code == dept_type_code
            )

        return departments

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
