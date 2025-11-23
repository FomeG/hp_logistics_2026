from odoo.addons.component.core import Component
from odoo.addons.hp_components.models.constants import LocationType

class LocationBaseListener(Component):
    _name = "hp_components.location.base.listener"
    _description = "Location listener"
    _inherit = 'base.event.listener'
    _apply_on = ['location.base']

    def on_record_create(self, record, fields=None):
        if record.type == LocationType.PORT:
            self.env['route.base'].create_freight_sea_from_port(record)
