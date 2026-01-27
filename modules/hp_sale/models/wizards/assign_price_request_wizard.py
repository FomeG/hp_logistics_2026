from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AssignPriceRequestWizard(models.TransientModel):
    _name = 'assign.price.request.wizard'
    _description = 'Assign Price Request Wizard'

    price_request_id = fields.Many2one(
        'freight.purchase.sea.freight.request',
        string='Price Request',
        required=True
    )

    assignee_id = fields.Many2one(
        'res.users',
        string='Assign To',
        required=True,
    )

    allowed_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_allowed_user_ids',
        store=False,
    )

    @api.model
    def default_get(self, fields_list):
        """Override default_get to populate allowed_user_ids when form opens"""
        defaults = super().default_get(fields_list)
        if 'allowed_user_ids' in fields_list:
            allowed_ids = self._get_allowed_user_ids()
            defaults['allowed_user_ids'] = [(6, 0, allowed_ids)]
        return defaults

    @api.depends_context('uid')
    def _compute_allowed_user_ids(self):
        """Compute users from departments managed by current user (DOPR)"""
        allowed_ids = self._get_allowed_user_ids()
        for rec in self:
            rec.allowed_user_ids = [(6, 0, allowed_ids)]

    @api.model
    def _get_allowed_user_ids(self):
        """
        Get user IDs from all pricing departments managed by the current user.
        Similar to hr_team logic for _get_allowed_department_ids.

        - Admin and CEO: can see all pricing members
        - DOPR (pricing leader): can see members from departments they manage

        Returns list of user IDs.
        """
        current_user = self.env.user

        # Admin users and CEO can see all pricing users
        is_admin = current_user.has_group('base.group_system')
        is_ceo = current_user.has_group('hp_components.ceo')

        if is_admin or is_ceo:
            # Find all employees in pricing departments with user accounts
            pricing_departments = self.env['hr.department'].sudo().search([
                ('department_type_id.code', '=', 'pricing')
            ])
            employees = self.env['hr.employee'].sudo().search([
                ('department_id', 'in', pricing_departments.ids),
                ('user_id', '!=', False)
            ])
            return employees.mapped('user_id').ids

        # For DOPR (pricing leaders): find pricing departments they manage
        # Similar to hr_team logic: search departments where manager_id.user_id = current user
        managed_departments = self.env['hr.department'].sudo().search([
            ('manager_id.user_id', '=', current_user.id),
            ('department_type_id.code', '=', 'pricing')
        ])

        if not managed_departments:
            # If user doesn't manage any pricing department, return empty
            # (they shouldn't be able to access this wizard anyway)
            return []

        # Get all employees from these managed pricing departments with user accounts
        employees_in_managed_depts = self.env['hr.employee'].sudo().search([
            ('department_id', 'in', managed_departments.ids),
            ('user_id', '!=', False)
        ])

        # Get user IDs from these employees
        user_ids = employees_in_managed_depts.mapped('user_id').ids

        return user_ids

    def action_confirm(self):
        """Assign the price request to the selected user"""
        self.ensure_one()

        if not self.assignee_id:
            raise ValidationError(_('Please select a user to assign this price request.'))

        # Update assignee on price request
        self.price_request_id.write({
            'assignee_id': self.assignee_id.id
        })

        # Post message to chatter
        self.price_request_id.message_post(
            body=_('Price request reassigned to %s by %s') % (
                self.assignee_id.name,
                self.env.user.name
            )
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Price request assigned to %s') % self.assignee_id.name,
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
