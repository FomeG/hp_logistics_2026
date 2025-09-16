# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ZaloGPSWebhookController(http.Controller):
    """Controller to handle GPS location data from CRM system"""
    @http.route('/zalo/gps_location', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_gps_location(self, **post):
        try:
            # Get JSON data from request
            data = request.jsonrequest
            if not data:
                return self._error_response("No JSON data received")

            # Validate required fields
            required_fields = ['phone', 'longitude', 'latitude']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return self._error_response(f"Missing required fields: {', '.join(missing_fields)}")

            phone = data.get('phone', '').strip()
            longitude = float(data.get('longitude'))
            latitude = float(data.get('latitude'))
            
            # Validate coordinates
            if not (-180 <= longitude <= 180):
                return self._error_response("Longitude must be between -180 and 180 degrees")
            
            if not (-90 <= latitude <= 90):
                return self._error_response("Latitude must be between -90 and 90 degrees")

            # Find driver by phone number
            driver = request.env['trucking_planning.driver'].sudo().search([
                ('phone_number', '=', phone)
            ], limit=1)
            
            if not driver:
                _logger.warning(f"GPS webhook: Driver not found for phone {phone}")
                return self._error_response(f"Driver not found for phone number: {phone}")

            # Find current trip for this driver
            trip = request.env['trucking_planning.trip'].sudo().search([
                ('driver_id', '=', driver.id),
                ('is_current', '=', True),
                ('status', 'not in', ['cancelled', 'done'])
            ], limit=1)
            
            if not trip:
                _logger.warning(f"GPS webhook: No current trip found for driver {driver.name} (phone: {phone})")
                return self._error_response(f"No current trip found for driver {driver.name}")

            # Prepare checkpoint data - simplified to only trip_id and location
            checkpoint_data = {
                'trip_id': trip.id,
                'longitude': longitude,
                'latitude': latitude,
            }

            # Create checkpoint record
            checkpoint = request.env['trucking_planning.trip_checkpoint'].sudo().create(checkpoint_data)

            _logger.info(
                f"GPS checkpoint created successfully: "
                f"Checkpoint ID: {checkpoint.id}, Trip ID: {trip.id}, "
                f"Driver: {driver.name}, Location: {latitude}, {longitude}"
            )

            return {
                'success': True,
                'message': f'GPS location recorded successfully for trip {trip.code or trip.id}',
                'checkpoint_id': checkpoint.id,
                'trip_id': trip.id,
                'driver_id': driver.id,
                'trip_code': trip.code or f'Trip {trip.id}',
                'driver_name': driver.name
            }

        except ValidationError as e:
            _logger.error(f"GPS webhook validation error: {str(e)}")
            return self._error_response(f"Validation error: {str(e)}")
        
        except Exception as e:
            _logger.error(f"GPS webhook error: {str(e)}", exc_info=True)
            return self._error_response(f"Internal server error: {str(e)}")

    def _error_response(self, message):
        """Helper method to return error response"""
        return {
            'success': False,
            'message': message,
            'checkpoint_id': None,
            'trip_id': None,
            'driver_id': None
        }

    @http.route('/zalo/test', type='json', auth='none', methods=['GET'], cors = '*', csrf=False)

    def test_zalo_webhook(self):
        """Test endpoint to verify webhook is working"""
        return http.Response(
            json.dumps({
                'status': 'ok',
                'message': 'Zalo GPS webhook endpoint is accessible',
                'timestamp': fields.Datetime.now().isoformat()
            }),
            content_type='application/json'
        )
