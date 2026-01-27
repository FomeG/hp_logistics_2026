from odoo.addons.component.core import Component

class SeaFreightRequestListener(Component):
    _name = 'freight.purchase.sea.freight.request.listener.pricing'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.sea.freight.request']

    def on_record_create(self, record, fields=None):
        record.with_delay()._update_assignee()
        return