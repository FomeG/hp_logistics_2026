from odoo.addons.component.core import Component
from ..services.freight_warehouse_service import FreightWarehouseService

class FreightPurchaseBookingListener(Component):
    _name = 'custom_component.freight_puchase_booking_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking']

    def on_record_write(self, record, fields=None):
        if 'status' in fields:
            old_status = record.env.context.get('old_status')
            new_satus = record.status
            service = FreightWarehouseService(self.env)

            if old_status in {'draft', 'pending'} and new_satus in {'confirmed', 'fully_assigned', 'shipped'}:
                service.create_warehouse_by_booking(record, 'out')

            if old_status in {'confirmed', 'fully_assigned', 'shipped'} and new_satus in {'cancelled', 'expired'}:
                service.create_warehouse_by_booking(record, 'return')  
        return
                