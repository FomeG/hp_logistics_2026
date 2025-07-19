from odoo.addons.component.core import Component
from ..services.freight_purchase_quotation_service import FreightPurchaseQuotationService

import logging
_logger = logging.getLogger(__name__)

class FreightPurchaseBookingListener(Component):
    _name = 'freight.purchase.booking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking']

    def on_record_create(self, record, fields=None):
        """Auto-trigger quotation creation from fees for bookings without quotation"""
        quotation_service = FreightPurchaseQuotationService(self.env)
        
        if (record.booking_mode == 'without_quotation' and 
            record.has_fees and 
            not record.quotation_id):
            quotation_service.auto_create_quotation_from_booking_fees(record)
        
        return

    def on_record_write(self, record, fields=None):
        """Auto-trigger quotation creation from fees if conditions are met"""
        quotation_service = FreightPurchaseQuotationService(self.env)
        
        if (record.booking_mode == 'without_quotation' and 
            record.has_fees and 
            not record.quotation_id):
            quotation_service.auto_create_quotation_from_booking_fees(record)
        
        return
