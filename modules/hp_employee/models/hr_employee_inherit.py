from odoo import models, api

class HREmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            work_email = vals.get("work_email")
            if (work_email):
                existing_user = self.env["res.users"].search([("login", "=", work_email)], limit=1)
                if not existing_user:
                    user_vals = {
                        "name": vals.get("name", "New User"),
                        "login": work_email,
                        "email": work_email,
                        "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
                    }
                    new_user = self.env["res.users"].create(user_vals)
                    vals["user_id"] = new_user.id
                else:
                    vals["user_id"] = existing_user.id

        return super().create(vals_list)
