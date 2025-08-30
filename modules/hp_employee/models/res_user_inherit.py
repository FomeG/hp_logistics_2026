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

    def write(self, vals):
        # Sync user changes to employee (if employee exists and values are different)
        sync_fields = {}
        for user in self:
            if user.employee_id:
                if 'name' in vals and vals['name'] and vals['name'] != user.employee_id.name:
                    sync_fields['name'] = vals['name']
                if 'email' in vals and vals['email'] and vals['email'] != user.employee_id.work_email:
                    sync_fields['work_email'] = vals['email']
                if 'phone' in vals and vals['phone'] and vals['phone'] != user.employee_id.mobile_phone:
                    sync_fields['mobile_phone'] = vals['phone']
        
        # Perform the user update first
        result = super().write(vals)
        
        # Then sync to employee if needed
        if sync_fields:
            for user in self:
                if user.employee_id:
                    user.employee_id.write(sync_fields)
        
        return result

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

