from odoo import models, fields


class PlanPrefixRule(models.Model):
    _name = "trucking_planning.plan.prefix.rule"
    _description = "Prefix Rule for Plan Code"
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Prefix',
        tracking=True,
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string="User"
    )
