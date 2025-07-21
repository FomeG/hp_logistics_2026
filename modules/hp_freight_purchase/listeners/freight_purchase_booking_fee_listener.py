from odoo.addons.component.core import Component
from ..services.freight_purchase_quotation_service import FreightPurchaseQuotationService

import logging
_logger = logging.getLogger(__name__)

class FreightPurchaseBookingFeeListener(Component):
    _name = 'freight.purchase.booking.fee.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking.fee']

    def on_record_create(self, record, fields=None):
        """Sync booking fee to quotation fee when created"""
        quotation_service = FreightPurchaseQuotationService(self.env)
        quotation_service.sync_booking_fee_to_quotation(record)
        return

    def on_record_write(self, record, fields=None):
        """Sync booking fee to quotation fee when updated"""
        if 'amount' in fields or 'note' in fields:
            quotation_service = FreightPurchaseQuotationService(self.env)
            quotation_service.sync_booking_fee_to_quotation(record)
        return 