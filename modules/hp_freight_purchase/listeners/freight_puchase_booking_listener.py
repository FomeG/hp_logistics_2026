from odoo.addons.component.core import Component
from ..services.freight_purchase_booking_inventory_service import FreightPurchaseBookingInventoryService
from ..models.freight_purchase_booking_inventory import FreightPurchaseBookingInventory
class FreightPurchaseBookingListener(Component):
    _name = 'custom_component.freight_puchase_booking_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking']

    def on_record_write(self, record, fields=None):
        if 'status' in fields:
            old_status = record.env.context.get('old_status')
            new_satus = record.status
            service = FreightPurchaseBookingInventoryService(self.env)
            action = False
            if old_status in {'draft', 'pending'} and new_satus in {'confirmed', 'fully_assigned', 'shipped'}:
                action = FreightPurchaseBookingInventory.ACTION_OUT
            if old_status in {'confirmed', 'fully_assigned', 'shipped'} and new_satus in {'cancelled', 'expired'}:
                action = FreightPurchaseBookingInventory.ACTION_RETURN
            if action:
                service.create_inventory_by_booking(record, action)
        return
                