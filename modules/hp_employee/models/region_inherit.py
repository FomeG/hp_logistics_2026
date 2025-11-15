from odoo import models, fields, api

class RegionInherit(models.Model):
    _inherit = ['region']

    team_ids = fields.One2many(
        'hr.team',
        'region_id',
        string="Teams"
    )
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Members',
        tracking=True
    )
    employee_string = fields.Char(
        string="Employees in Region",
        compute='_compute_employee_string',
        store=False
    )
    @api.depends('employee_ids')
    def _compute_employee_string(self):
        for region in self:
            if region.employee_ids:
                region.employee_string = ", ".join(region.employee_ids.mapped('name'))
            else:
                region.employee_string = ""