from odoo.addons.component.core import Component
from odoo.exceptions import ValidationError

class SeaFreightRequestListener(Component):
    _name = 'freight.purchase.sea.freight.request.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.sea.freight.request']

    def on_record_create(self, record, fields=None):
        record.with_delay()._handle_notify_on_create()
        return