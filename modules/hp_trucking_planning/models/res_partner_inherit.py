from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ...hp_components.services.department_service import DepartmentService
from ..services.res_partner_service import ResPartnerService

class ResPartnerInherit(models.Model):
    _inherit = ['res.partner']

    type = fields.Selection([
        ('contact', 'Contact'),
        ('invoice', 'Invoice Address'),
        ('delivery', 'Delivery Address'),
        ('other', 'Other Address'),
        (ResPartnerService.PARTNER_TYPE_DRIVER, 'Driver'),
        (ResPartnerService.PARTNER_TYPE_CLIENT, 'Client'),
    ],string='Address Type', default='contact')

    # ====== Start Driver ======
    cccd = fields.Char(string='CCCD', tracking=True)
    license_number = fields.Char(string='License Number', tracking=True)
    contract_date = fields.Date(string='Contract Date', tracking=True)
    notes = fields.Text(string='Notes')
    # ====== End Driver ======

    # ====== Start Client ======
    code = fields.Char(string= 'Client Code', tracking=True)
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
        tracking=True,
    )
    branch_id = fields.Many2one(
        comodel_name='trucking_planning.branch',
        index=True,
        string='Branch',
        tracking=True,
        default=lambda self: self.env.user.branch_ids[:1].id,
    )
    can_edit_assign_user = fields.Boolean(compute="_compute_can_edit_assign_user", store=False)
    # ====== End Client ======

    _sql_constraints = [
        ('unique_license_number', 'UNIQUE(license_number)','License Number must be unique!'),
        ('unique_cccd', 'UNIQUE(cccd)', 'CCCD must be unique!'),
        ('unique_phone', 'UNIQUE(phone)', 'Phone Number must be unique!'),
        ('unique_vat', 'UNIQUE(vat)','Tax Number must be unique!'),
    ]

    _required_fields_by_type = {
        ResPartnerService.PARTNER_TYPE_DRIVER: ['name', 'cccd', 'license_number'],
        ResPartnerService.PARTNER_TYPE_CLIENT: ['name', 'code', 'vat', 'branch_id'],
    }

    @api.constrains('type')
    def _check_required_fields_by_type(self):
        for rec in self:
            required_fields = self._required_fields_by_type.get(rec.type, [])
            missing = [field for field in required_fields if not rec[field]]
            if missing:
                raise ValidationError(
                    f"When type is '{rec.type}', the following fields are required: {', '.join(missing)}"
                )

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