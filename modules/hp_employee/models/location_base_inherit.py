from odoo import models, fields, api

class LocationBaseInherit(models.Model):
    _inherit = ['location.base']

    team_ids = fields.Many2many(
        'hr.team',
        'hr_team_location_rel',
        'location_id', 'team_id',
        string="Teams",
    )