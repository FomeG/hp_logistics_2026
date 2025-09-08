from odoo import models, fields

class ResUsersInherit(models.Model):
    _inherit = "res.users"

    branch_ids = fields.Many2many(
        comodel_name="trucking_planning.branch",
        string="Branches",
    )