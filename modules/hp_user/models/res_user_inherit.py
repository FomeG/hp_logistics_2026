from odoo import models, api

class ResUserInherit(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)

        employee_vals_list = []
        for user in users:
            employee_vals_list.append({
                'name': user.name,
                'work_email': user.email,
                'user_id': user.id,
                'company_id': user.company_id.id if user.company_id else False,
                'active': True,
            })

        if employee_vals_list:
            self.env['hr.employee'].create(employee_vals_list)

        return users