from odoo import models, api

class ResUserInherit(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        user = super(ResUserInherit, self).create(vals)

        employee_vals = {
            'name': user.name,
            'work_email': user.email,
            'user_id': user.id,
            'company_id': user.company_id.id if user.company_id else False,
            'active': True,
        }
        self.env['hr.employee'].create(employee_vals)
        return user