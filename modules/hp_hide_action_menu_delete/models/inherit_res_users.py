from odoo import api, fields, models

class InheritResUsers(models.Model):
    _inherit = "res.users"

    is_hide_delete = fields.Boolean(string="Hide All", default=True)
    applied_delete_models_ids = fields.Many2many(
        comodel_name="ir.model", string="Applied Models"
    )

    @api.model
    def get_is_hide_delete_and_applied_models(self):
        current_user = self.env.user

        is_hide_delete = current_user.is_hide_delete
        applied_delete_models = []
        for model in current_user.applied_delete_models_ids:
            applied_delete_models.append((model.id, model.model if model else False))

        return {
            "is_hide_delete": is_hide_delete,
            "applied_delete_models_ids": applied_delete_models,
        }
