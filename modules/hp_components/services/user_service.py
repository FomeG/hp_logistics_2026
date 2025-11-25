from odoo import models, fields, api

class UserService(models.AbstractModel):
    _name = 'hp_components.user.service'
    _description = 'User Service'

    # current_user = fields.Many2one(
    #     comodel_name='res.users',
    #     string='Current User',
    #     default=lambda self: self.env.user,
    # )

    @api.model
    def is_admin_user(self, user_id=None):
        """Check if the given user (or current user if none provided) is an admin."""
        if user_id is None:
            user = self.env.user
        else:
            user = self.env['res.users'].browse(user_id)

        admin_group = self.env.ref('base.group_system', raise_if_not_found=False)
        return admin_group and admin_group in user.groups_id

    @api.model
    def _check_user_has_group(self, group_name, user_id=None):
        """Check if the given user (or current user if none provided) has the specified group."""
        if user_id is None:
            user = self.env.user
        else:
            user = self.env['res.users'].browse(user_id)

        return user.has_group(group_name)

    @api.model
    def is_salesman_member(self):
        """Check if the given user (or current user if none provided) is a salesman."""
        return self._check_user_has_group('sales_team.group_sale_salesman')

    @api.model
    def is_salesman_manager(self):
        """Check if the given user (or current user if none provided) is a sales manager."""
        return self._check_user_has_group('sales_team.group_sale_manager')

    @api.model
    def is_salesman_leader(self):
        """Check if the given user (or current user if none provided) is a salesman leader."""
        return self._check_user_has_group('sales_team.group_sale_salesman_all_leads')



