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
