# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class VehicleTrackingMapController(http.Controller):
    """Controller for vehicle tracking map display and data endpoints"""

    @http.route('/vehicle_tracking/map', type='http', auth='user', website=True)
    def vehicle_tracking_map_view(self, **kwargs):
        """
        Main map view page
        Displays live vehicle tracking map with OpenStreetMap + Leaflet.js
        """
        return request.render('hp_vehicle_tracking.vehicle_tracking_map_template', {
            'page_name': 'vehicle_tracking_map',
        })

    @http.route('/vehicle_tracking/api/driver_locations', type='json', auth='user', methods=['POST'])
    def get_driver_locations(self, **kwargs):
        """
        JSON API endpoint to fetch latest location for each driver with current trip
        Uses service layer for business logic (following hp_trucking_planning convention)
        
        Returns:
            List of driver locations
        """
        try:
            # Use service layer for business logic
            tracking_service = request.env['vehicle.tracking.service']
            driver_locations = tracking_service.get_all_active_driver_locations()
            
            _logger.info(f"Vehicle tracking: Returned {len(driver_locations)} driver locations")
            
            return {
                'success': True,
                'data': driver_locations,
                'count': len(driver_locations),
                'timestamp': fields.Datetime.now().isoformat()
            }
            
        except Exception as e:
            _logger.error(f"Error fetching driver locations: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'count': 0
            }

    @http.route('/vehicle_tracking/api/trip_route/<int:trip_id>', type='json', auth='user', methods=['POST'])
    def get_trip_route(self, trip_id, **kwargs):
        """
        Get all checkpoints for a specific trip to display route history
        Uses service layer for business logic
        
        Args:
            trip_id: ID of the trip
            
        Returns:
            List of all checkpoints ordered by time
        """
        try:
            # Use service layer for business logic
            tracking_service = request.env['vehicle.tracking.service']
            route_points = tracking_service.get_trip_route_history(trip_id)
            
            return {
                'success': True,
                'trip_id': trip_id,
                'route_points': route_points,
                'count': len(route_points)
            }
            
        except Exception as e:
            _logger.error(f"Error fetching trip route: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'route_points': []
            }

    @http.route('/vehicle_tracking/api/stats', type='json', auth='user', methods=['POST'])
    def get_tracking_stats(self, **kwargs):
        """
        Get statistics for the tracking dashboard
        Uses service layer for business logic
        
        Returns:
            Dashboard statistics
        """
        try:
            # Use service layer for business logic
            tracking_service = request.env['vehicle.tracking.service']
            stats = tracking_service.get_tracking_statistics()
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            _logger.error(f"Error fetching tracking stats: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'stats': {}
            }

