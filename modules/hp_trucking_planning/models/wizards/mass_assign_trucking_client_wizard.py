from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_components.services.department_service import DepartmentService


class MassAssignTruckingUserWizard(models.TransientModel):
    _name = 'assign.trucking.client.wizard'
    _description = 'Bulk assign trucking user and branch to trucking client'

    client_ids = fields.Many2many(
        'res.partner.client',
        string='Selected Clients',
        readonly=True
    )
    branch_id = fields.Many2one(
        'trucking_planning.branch',
        string='Trucking Branch',
        required=True,
    )

    assign_user_id = fields.Many2one(
        'res.users',
        string='Assign User',
        required=True,
        domain="[('id', 'in', allowed_user_ids)]"
    )
    allowed_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_allowed_user_ids',
        store=False
    )

    @api.depends('branch_id')
    def _compute_allowed_user_ids(self):
        dept_service = DepartmentService(self.env)
        for wizard in self:
            trucking_users = dept_service.get_user_by_department_type(dept_service.DEPARTMENT_TYPE_TRUCKING)
            if wizard.branch_id:
                trucking_users = trucking_users.filtered(lambda u: wizard.branch_id.code in u.branch_ids.mapped('code'))
            wizard.allowed_user_ids = trucking_users

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.assign_user_id = False

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            defaults['client_ids'] = [(6, 0, self.env.context['active_ids'])]
        if 'branch_id' in fields_list and not defaults.get('branch_id'):
            trucking_branch = self.env['trucking_planning.branch'].search(
                [('code', '=', self.env.user.branch_ids[:1].code)], limit=1)
            defaults['branch_id'] = trucking_branch.id
        return defaults

    def action_assign_trucking_users(self):
        self.ensure_one()
        if not self.client_ids:
            raise UserError(_('No clients selected.'))

        self.client_ids.write({
            'assign_trucking_manager_id': self.assign_user_id.id,
            'trucking_branch_id': self.branch_id.id,
        })
        updated_count = len(self.client_ids)

        message = _('Successful updated %s trucking clients (Branch: %s).') % (
            updated_count, self.branch_id.name if self.branch_id else 'Tất cả',
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Trucking Client Assignment Successful'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }