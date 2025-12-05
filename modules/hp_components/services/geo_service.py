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
    @api.model
    def get_or_create_location_by_name(self, name, country_id=None, **additional_kwargs):
        location = self.env['location.base'].search([
            ('name', '=ilike', name),
            ('country_id', '=', country_id.id) if country_id else ('id', '!=', False)
        ], limit=1)
        if not location:
            location = self.env['location.base'].create({
                'name': name,
                'address': additional_kwargs.get('address', ''),
                'type': additional_kwargs.get('type', LocationType.OTHER),
                'contact_name': additional_kwargs.get('contact_name', ''),
                'contact_phone': additional_kwargs.get('contact_phone', ''),
                'extra_fuel': additional_kwargs.get('extra_fuel', False),
                'state_id': additional_kwargs.get('state_id', False),
                'country_id': country_id.id if country_id else False,
                'longitude': additional_kwargs.get('longitude', 0.0),
                'latitude': additional_kwargs.get('latitude', 0.0),
                'parent_id': additional_kwargs.get('parent_id', False),
            })
        return location

    @api.model
    def get_or_create_route_between_locations(self, from_location, to_location, **additional_kwargs):
        route = self.env['route.base'].search([
            '|',
            '&', ('from_location_id', '=', from_location.id),
            ('to_location_id', '=', to_location.id),
            '&', ('from_location_id', '=', to_location.id),
            ('to_location_id', '=', from_location.id),
        ], limit=1)
        if not route:
            route = self.env['route.base'].create({
                'from_location_id': from_location.id,
                'to_location_id': to_location.id,
            })
        return route