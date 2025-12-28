from odoo import models, fields, api

class UserService(models.AbstractModel):
    _name = 'hp_components.user.service'
    _description = 'User Service'

    @api.model
    def _get_user(self, user_id=None):
        """Get the user record. If user_id is None, returns the current user."""
        if user_id is None:
            return self.env.user
        return self.env['res.users'].browse(user_id)

    @api.model
    def _check_user_has_group(self, group_name, user_id=None):
        """Check if the given user (or current user if none provided) has the specified group."""
        user = self._get_user(user_id)
        return user.has_group(group_name)

    @api.model
    def is_admin_user(self, user_id=None):
        """Check if the given user (or current user if none provided) is an admin (system group)."""
        return self._check_user_has_group('base.group_system', user_id)

    @api.model
    def is_salesman_member(self, user_id=None):
        """Check if the given user (or current user if none provided) is a salesman."""
        return self._check_user_has_group('sales_team.group_sale_salesman', user_id)

    @api.model
    def is_salesman_manager(self, user_id=None):
        """Check if the given user (or current user if none provided) is a sales manager."""
        return self._check_user_has_group('sales_team.group_sale_manager', user_id)

    @api.model
    def is_salesman_leader(self, user_id=None):
        """Check if the given user (or current user if none provided) is a salesman leader."""
        return self._check_user_has_group('sales_team.group_sale_salesman_all_leads', user_id)


    @api.model
    def is_only_salesman(self, user_id=None):

        is_salesman = self.is_salesman_member(user_id)
        is_leader = self.is_salesman_leader(user_id)
        is_manager = self.is_salesman_manager(user_id)

        return is_salesman and not is_leader and not is_manager


