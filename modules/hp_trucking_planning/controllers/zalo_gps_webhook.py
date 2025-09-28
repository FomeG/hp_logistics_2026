# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ZaloGPSWebhookController(http.Controller):
    """Controller to handle GPS location data from CRM system"""

    @http.route('/zalo/gps_location', type='http', auth='public', csrf=False, methods=['POST'], cors='*')
    def receive_gps_location(self, **post):
        try:
            # Get JSON data from request
            response_data = json.loads(request.httprequest.data.decode('utf-8'))
            print(f'response_data: {response_data}')
            
            if not response_data:
                return http.Response(
                    json.dumps(self._error_response("No JSON data received")),
                    content_type='application/json',
                    status=400
                )

            # Check if there's an error in the response
            if response_data.get('error', False):
                error_msg = response_data.get('message', 'Unknown error from CRM')
                _logger.error(f"CRM returned error: {error_msg}")
                return http.Response(
                    json.dumps(self._error_response(f"CRM error: {error_msg}")),
                    content_type='application/json',
                    status=400
                )

            # Extract the actual data from nested structure
            data = response_data.get('data', {})
            if not data:
                return http.Response(
                    json.dumps(self._error_response("No data field found in response")),
                    content_type='application/json',
                    status=400
                )

            # Validate required fields in the nested data
            required_fields = ['phone', 'longitude', 'latitude']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return http.Response(
                    json.dumps(self._error_response(f"Missing required fields in data: {', '.join(missing_fields)}")),
                    content_type='application/json',
                    status=400
                )

            phone = data.get('phone', '').strip()
            longitude = float(data.get('longitude'))
            latitude = float(data.get('latitude'))

            # Validate coordinates
            if not (-180 <= longitude <= 180):
                return http.Response(
                    json.dumps(self._error_response("Longitude must be between -180 and 180 degrees")),
                    content_type='application/json',
                    status=400
                )
            
            if not (-90 <= latitude <= 90):
                return http.Response(
                    json.dumps(self._error_response("Latitude must be between -90 and 90 degrees")),
                    content_type='application/json',
                    status=400
                )

            # Find driver by phone number (handle both international and local formats)
            driver = None
            
            # First try exact match
            driver = request.env['res.partner.driver'].sudo().search([
                ('phone', '=', phone)
            ], limit=1)
            
            # If not found and phone starts with '84', try converting to local format
            if not driver and phone.startswith('84'):
                # Convert 84965774192 -> 0965774192
                local_phone = '0' + phone[2:]  # Remove '84' prefix and add '0'
                driver = request.env['res.partner.driver'].sudo().search([
                    ('phone', '=', local_phone)
                ], limit=1)
                if driver:
                    _logger.info(f"GPS webhook: Found driver using local format {local_phone} for international phone {phone}")
            
            # If still not found and phone starts with '0', try converting to international format
            elif not driver and phone.startswith('0'):
                # Convert 0965774192 -> 84965774192
                international_phone = '84' + phone[1:]  # Remove '0' prefix and add '84'
                driver = request.env['res.partner.driver'].sudo().search([
                    ('phone', '=', international_phone)
                ], limit=1)
                if driver:
                    _logger.info(f"GPS webhook: Found driver using international format {international_phone} for local phone {phone}")
            
            if not driver:
                _logger.warning(f"GPS webhook: Driver not found for phone {phone}")
                return http.Response(
                    json.dumps(self._error_response(f"Driver not found for phone number: {phone}")),
                    content_type='application/json',
                    status=404
                )

            # Find current trip for this driver
            trip = request.env['trucking_planning.trip'].sudo().search([
                ('driver_id', '=', driver.id),
                ('is_current', '=', True),
                ('status', 'not in', ['cancelled', 'done'])
            ], limit=1)
            
            if not trip:
                _logger.warning(f"GPS webhook: No current trip found for driver {driver.name} (phone: {phone})")
                return http.Response(
                    json.dumps(self._error_response(f"No current trip found for driver {driver.name}")),
                    content_type='application/json',
                    status=404
                )

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

            return http.Response(
                json.dumps({
                    'success': True,
                    'message': f'GPS location recorded successfully for trip {trip.code or trip.id}',
                    'checkpoint_id': checkpoint.id,
                    'trip_id': trip.id,
                    'driver_id': driver.id,
                    'trip_code': trip.code or f'Trip {trip.id}',
                    'driver_name': driver.name
                }),
                content_type='application/json',
                status=200
            )

        except ValidationError as e:
            _logger.error(f"GPS webhook validation error: {str(e)}")
            return http.Response(
                json.dumps(self._error_response(f"Validation error: {str(e)}")),
                content_type='application/json',
                status=400
            )
        
        except Exception as e:
            _logger.error(f"GPS webhook error: {str(e)}", exc_info=True)
            return http.Response(
                json.dumps(self._error_response(f"Internal server error: {str(e)}")),
                content_type='application/json',
                status=500
            )

    def _error_response(self, message):
        """Helper method to return error response"""
        return {
            'success': False,
            'message': message,
            'checkpoint_id': None,
            'trip_id': None,
            'driver_id': None
        }

    @http.route('/zalo/test', type='http', auth='public', methods=['GET'], cors='*', csrf=False)

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
