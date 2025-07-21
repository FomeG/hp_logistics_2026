from odoo.addons.component.core import Component
from ..services.freight_purchase_quotation_service import FreightPurchaseQuotationService

import logging
_logger = logging.getLogger(__name__)

class FreightPurchaseBookingLineFeeListener(Component):
    _name = 'freight.purchase.booking.line.fee.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking.line.fee']

    def on_record_create(self, record, fields=None):
        """Sync booking line fee to quotation line fee when created"""
        quotation_service = FreightPurchaseQuotationService(self.env)
        quotation_service.sync_booking_line_fee_to_quotation(record)
        return

    def on_record_write(self, record, fields=None):
        """Sync booking line fee to quotation line fee when updated"""
        if 'amount' in fields:
            quotation_service = FreightPurchaseQuotationService(self.env)
            quotation_service.sync_booking_line_fee_to_quotation(record)
        return 