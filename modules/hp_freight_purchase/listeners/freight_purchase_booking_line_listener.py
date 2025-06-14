from datetime import timedelta
from odoo import fields
from odoo.addons.component.core import Component

import logging
_logger = logging.getLogger(__name__)
class FreightPurchaseBookingLineListener(Component):
    _name = 'freight.purchase.booking.line.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.booking.line']

    def on_change_sale_order_line(self, record, origin_sale_order_lines, new_sale_order_lines):
        self._compute_expiration(record,origin_sale_order_lines, new_sale_order_lines)
        self._compute_booking_line_history(record,origin_sale_order_lines, new_sale_order_lines)

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
    def _compute_booking_line_history(self, record, origin_sale_order_lines, new_sale_order_lines):
        _logger.info('_compute_booking_line_history')