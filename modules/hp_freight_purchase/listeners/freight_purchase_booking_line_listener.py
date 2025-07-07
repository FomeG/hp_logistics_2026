from datetime import timedelta
from odoo import fields
from odoo.addons.component.core import Component
from ..services.freight_purchase_booking_inventory_service import FreightPurchaseBookingInventoryService
from ..models.freight_purchase_booking_inventory import FreightPurchaseBookingInventory

import logging
_logger = logging.getLogger(__name__)
class FreightPurchaseBookingLineListener(Component):
    _name = 'freight.purchase.booking.line.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking.line']

    def on_change_sale_order_line(self, record, origin_sale_order_lines, new_sale_order_lines):
        self._compute_expiration(record,origin_sale_order_lines, new_sale_order_lines)

    def _compute_expiration(self, record, origin_sale_order_lines, new_sale_order_lines):
        deadline = record.RESERVATION_DEADLINE_HOURS
        if deadline > 0:
            origin_lines = set(origin_sale_order_lines)
            new_lines = set(new_sale_order_lines)
            if origin_lines != new_lines:
                if new_lines:
                    record.write({
                        'reservation_expiration_date': fields.Datetime.now() + timedelta(hours=deadline)
                    })
                else:
                    record.write({
                        'reservation_expiration_date': False
                    })
    def on_record_write(self, record, fields=None):
        if 'status' in fields:
            old_status = record.env.context.get('old_status')
            new_satus = record.status
            service = FreightPurchaseBookingInventoryService(self.env)
            action = None
            if old_status in {'available', 'reserved', 'allocated', 'shipped'} and new_satus in {'cancelled'}:
                action = FreightPurchaseBookingInventory.ACTION_RETURN

            service.create_inventory_by_booking_line(record, action)
        return

    def on_record_create(self, record, fields=None):
        status = record.status
        service = FreightPurchaseBookingInventoryService(self.env)
        if status in {'available', 'reserved', 'allocated', 'shipped'}:
            action = FreightPurchaseBookingInventory.ACTION_OUT
            service.create_inventory_by_booking_line(record, action) 

        return
