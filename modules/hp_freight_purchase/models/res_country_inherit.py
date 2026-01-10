# res.country extension
from odoo import models, fields

class ResCountryInherit(models.Model):
    _inherit = 'res.country'

    region_id = fields.Many2one(
        'region',
        string='Region',
        ondelete='set null'
    )
    port_ids = fields.One2many(
        'location.base',
        'country_id',
        string='Ports'
    )