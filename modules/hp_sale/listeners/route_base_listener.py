from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)

class RouteBaseListener(Component):
    _name = 'route.base.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['route.base']

    def on_record_create(self, record, fields=None):
        self.env['product.template'].get_or_create_from_route_base(record)

    def on_record_write(self, record, fields=None):
        self.env['product.template'].sync_with_route_base(record)