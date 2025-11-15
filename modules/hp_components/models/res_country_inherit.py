# res.country extension
from odoo import models, fields

class ResCountryInherit(models.Model):
    _inherit = 'res.country'

    region_id = fields.Many2one(
        comodel_name='region',
        string='Region',
        ondelete='cascade'
    )