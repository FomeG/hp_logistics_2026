from odoo import models, fields

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    user_id = fields.Many2one(default=lambda self: self.env.user)