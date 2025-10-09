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
            _logger.info(f'GPS Webhook received data: {response_data}')
            
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

            # Use service layer for business logic (following hp_trucking_planning convention)
            tracking_service = request.env['vehicle.tracking.service'].sudo()
            result = tracking_service.create_gps_checkpoint(phone, latitude, longitude)
            
            return http.Response(
                json.dumps({
                    'success': True,
                    'message': f'GPS location recorded successfully for trip {result["trip_code"]}',
                    'checkpoint_id': result['checkpoint_id'],
                    'trip_id': result['trip_id'],
                    'driver_id': result['driver_id'],
                    'trip_code': result['trip_code'],
                    'driver_name': result['driver_name']
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

