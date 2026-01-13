from odoo.addons.component.core import Component
from ...hp_components.models import constants

class SaleOrderListener(Component):
    _name = 'sale.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']

    def on_record_write(self, record, fields=None):
        if 'booking_line_id' in (fields or []):
            record.with_delay()._notify_assign_booking()
        
        return
            
