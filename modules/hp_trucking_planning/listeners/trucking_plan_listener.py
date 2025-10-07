# hp_trucking_planning/components/trucking_plan_listener.py
from odoo.addons.component.core import Component
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class TruckingPlanListener(Component):
    _name = 'trucking.plan.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.plan']

    def on_record_create(self, record, fields=None):
        """
        Khi plan được tạo => tự động tạo booking trong freight.purchase.booking
        """
        try:
            booking_model = self.env['freight.purchase.booking']

            # Check xem đã tồn tại booking nào cùng số booking_bill_no chưa
            existing_booking = booking_model.search([
                ('booking_name', '=', record.booking_bill_no)
            ], limit=1)

            if existing_booking:
                _logger.info(f"Booking already exists for {record.booking_bill_no}, skip auto-creation.")
                return

            # Dữ liệu tạo booking
            booking_vals = {
                'booking_mode': 'without_quotation',
                'booking_name': record.booking_bill_no or record.name,
                'vessel_id': 1,
                'quotation_id': False,
                'status': 'draft',
                'note': f"Auto-created from Trucking Plan {record.name}",
                'shipping_line_id': record.shipping_line_id.id,
                'quotation_shipping_line_id': record.shipping_line_id.id,
                'quotation_route_id': 1,
                'etd': datetime.now(),
            }

            booking = self.env['freight.purchase.booking'].with_context(skip_validator=True).create(booking_vals)
            record.write({'booking_id': booking.id})
            _logger.info(f"[Plan→Booking] Created booking {booking.name} for plan {record.name}")

            # Optional: lưu liên kết nếu bạn muốn reference 2 chiều
            record.message_post(body=f"Booking <b>{booking.name}</b> was auto-created from this plan.")

        except Exception as e:
            _logger.error(f"Error auto-creating booking from plan {record.name}: {str(e)}")
            self.env.cr.rollback()
