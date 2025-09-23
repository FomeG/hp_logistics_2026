from odoo import models, fields, api

class HrBranch(models.Model):
    _name = 'hr.branch'
    _description = 'Branch'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
    )
    plan_prefix = fields.Char(
        string="Plan Prefix",
        required=True,
        tracking=True,
    )

    _sql_constraints = [
        ('unique_plan_prefix', 'UNIQUE(plan_prefix)','Plan prefix must be unique!'),
    ]
    
