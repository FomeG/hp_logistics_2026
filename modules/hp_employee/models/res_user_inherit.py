from odoo import models, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        
        employee_id = self._context.get('default_create_employee_id')
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            if employee.exists():
                employee.user_id = users[0].id

        return users

    def _default_groups(self):
        """Override default groups for employee user creation"""
        # Check if this is being called from employee user creation context
        if self.env.context.get('employee_user_creation'):
            # Return only the basic user group without any implied admin groups
            basic_user_group = self.env.ref('base.group_user')
            return basic_user_group
        else:
            # Use the original default groups method
            return super()._default_groups()

