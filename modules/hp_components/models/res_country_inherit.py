# res.country extension
from odoo import models, fields
from odoo.addons.hp_components.models.constants import LocationType

class ResCountryInherit(models.Model):
    _inherit = 'res.country'

    region_id = fields.Many2one(
        comodel_name='region',
        string='Region',
        ondelete='set null',
    )
    location_base_ids = fields.One2many(
        comodel_name='location.base',
        string='Locations',
        inverse_name='country_id',
    )
    port_ids = fields.One2many(
        comodel_name='location.base',
        domain=[('type', '=', LocationType.PORT)],
        string='Ports',
        inverse_name='country_id',
    )

    port_count = fields.Integer(
        compute='_compute_port_count',
        string='Number of Ports',
    )
    def _compute_port_count(self):
        for record in self:
            record.port_count = len(record.port_ids)