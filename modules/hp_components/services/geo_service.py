from odoo import models, tools, api
from odoo.addons.hp_components.models.constants import LocationType

class GeoService(models.AbstractModel):

    _name = 'hp_components.geo.service'
    _description = 'geographical service'

    @tools.ormcache('country_code')
    def _get_country_by_code(self, country_code):
        return self.env['res.country'].search([
            ('code', '=', country_code),
        ],limit=1)
    @api.model
    def get_vietnam(self):
        return self._get_country_by_code('VN')

    @api.model
    def get_local_ports(self):
        return self.get_vietnam().port_ids

    @api.model
    def get_international_ports(self):
        vietnam = self.get_vietnam()
        return self.env['location.base'].search([
            ('type', '=', LocationType.PORT),
            ('country_id','!=',vietnam.id)
        ])