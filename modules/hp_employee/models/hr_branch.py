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
    branch_prefix = fields.Char(
        string="Branch Prefix",
        required=True,
        tracking=True,
    )

    department_ids = fields.One2many(
        comodel_name='hr.department',
        inverse_name='branch_id',
        string='Departments'
    )

    _sql_constraints = [
        ('unique_branch_prefix', 'UNIQUE(branch_prefix)','Branch prefix must be unique!'),
    ]
    
