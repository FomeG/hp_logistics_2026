from odoo import fields, _
from datetime import timedelta
import math
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.services.activity_service import ActivityService

import logging
_logger = logging.getLogger(__name__)

class FreightPurchaseBookingLineService:
    _name = "freight.purchase.booking.line.service"
    def __init__(self, env):
        self.env = env

    def reservation_expiration_reminder(self):
        now = fields.Datetime.now()
        # cancel
        expired_lines = self.env['freight.purchase.booking.line'].sudo().search([
            ('reservation_expiration_date', '<=', now),
            ('status', '!=', 'cancelled'),
        ])
        for expired_line in expired_lines:
            if self.is_booking_line_has_pending_sale_order(expired_line):
                expired_line.status = 'cancelled'
                self.send_notify_cancel(expired_line)

        # remind
        remind_booking_line = self.env['freight.purchase.remind'].sudo().search([
            ('type', '=', 'booking_line'),
            ('is_active', '=', True),
        ], limit=1)
        if not remind_booking_line:
            return
        
        total_remind = remind_booking_line.total
        interval_hour = remind_booking_line.interval
        max_ahead_time = now + timedelta(hours=total_remind * interval_hour)

        _logger.info('!!!!!!!!!!!!!!!!!')
        _logger.info(now)
        _logger.info(max_ahead_time)
        _logger.info('!!!!!!!!!!!!!!!!!')

        domain = [
            ('reservation_expiration_date', '>', now),
            ('reservation_expiration_date', '<=', max_ahead_time),
            ('reminder_count', '<', total_remind),
            ('status', '!=', 'cancelled'),
        ]

        without_booking_lines = remind_booking_line.without_booking_line_ids
        if without_booking_lines:
            domain.append(('id', 'not in', without_booking_lines.ids))

        booking_lines = self.env['freight.purchase.booking.line'].sudo().search(domain)
        for line in booking_lines:
            if not self.is_booking_line_has_pending_sale_order(line):
                continue

            time_left = line.reservation_expiration_date - now
            hours_left = time_left.total_seconds() / 3600.0
            expected_index = math.ceil(hours_left / interval_hour)

            _logger.info('!!!!!!!!!!!!!!!!!')
            _logger.info(expected_index)
            _logger.info(total_remind - line.reminder_count)
            _logger.info('!!!!!!!!!!!!!!!!!')

            if expected_index == (total_remind - line.reminder_count) and hours_left > 0:
                self.send_expiry_reminder(line)
                line.reminder_count += 1
    
    def is_booking_line_has_pending_sale_order(self, booking_line):
        return not booking_line.sale_order_line_ids or bool(
            booking_line.sale_order_line_ids.filtered(
                lambda sol: sol.order_id.state in ('draft', 'activated')
            )
        )
    
    def send_expiry_reminder(self, booking_line):
        creator = booking_line.create_uid
        if not creator:
            return

        service = ActivityService(
            env=self.env,
            model_name='freight.purchase.booking.line',
            record_id=booking_line.id,
            user_ids=creator.id
        )
    
        desciption = _(
            "Your booking <b>%s</b> is about to expire at <b>%s</b>.<br/>"
            "Please make sure the related Sale Orders are confirmed in time."
        ) % (booking_line.booking_id.name, fields.Datetime.to_string(booking_line.reservation_expiration_date))

        service._create_activity_by_type(
            activity_type_xml_id='mail.mail_activity_data_todo',
            summary='Upcoming Booking Expiration',
            note=desciption
        )
    
    def send_notify_cancel(self, booking_line):
        creator = booking_line.create_uid
        if not creator:
            return

        service = ActivityService(
            env=self.env,
            model_name='freight.purchase.booking.line',
            record_id=booking_line.id,
            user_ids=creator.id
        )

        service._create_activity_by_type(
            activity_type_xml_id='mail.mail_activity_data_todo',
            summary='Your booking line has been cancelled',
            note=''
        )
