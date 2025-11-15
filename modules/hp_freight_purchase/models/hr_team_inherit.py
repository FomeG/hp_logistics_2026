from odoo import models, fields, api

class HrTeamInherit(models.Model):
    _inherit = ['hr.team']

    region_id = fields.Many2one(
        comodel_name='region',
        string="Region",
        tracking=True,
        ondelete='set null'
    )