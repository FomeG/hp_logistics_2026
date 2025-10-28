from odoo.addons.component.core import Component

class FreightPurchaseBookingInventoryListener(Component):
    _name = 'freight.purchase.booking.inventory.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking.inventory']

    def on_booking_inventory_create(self, record, fields=None, **kwargs):
        if 'booking_inventory_form' in kwargs:
            record.create_quotation_line(kwargs['booking_inventory_form'])