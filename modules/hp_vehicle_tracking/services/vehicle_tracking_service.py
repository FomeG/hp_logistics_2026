# -*- coding: utf-8 -*-

import logging
from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class VehicleTrackingService(models.AbstractModel):
    """
    Service layer for vehicle tracking business logic
    Following hp_trucking_planning convention of using service layer for complex operations
    """
    _name = 'vehicle.tracking.service'
    _description = 'Vehicle Tracking Service'

    @api.model
    def get_driver_latest_location(self, driver_id):
        """
        Get the latest GPS location for a specific driver
        
        Args:
            driver_id: ID of the driver (res.partner)
            
        Returns:
            dict: Driver location data or None if not found
        """
        try:
            Trip = self.env['trucking_planning.trip']
            Checkpoint = self.env['trucking_planning.trip_checkpoint']
            
            # Find driver's current trip
            current_trip = Trip.search([
                ('driver_id', '=', driver_id),
                ('is_current', '=', True),
                ('status', 'not in', ['cancelled', 'done'])
            ], limit=1)
            
            if not current_trip:
                return None
            
            # Get latest checkpoint for this trip
            latest_checkpoint = Checkpoint.search([
                ('trip_id', '=', current_trip.id)
            ], order='create_date desc', limit=1)
            
            if not latest_checkpoint:
                return None
            
            # Calculate time difference
            now = fields.Datetime.now()
            time_diff = now - latest_checkpoint.create_date
            minutes_ago = int(time_diff.total_seconds() / 60)
            
            # Determine status based on freshness
            if minutes_ago <= 30:
                status = 'fresh'
            elif minutes_ago <= 60:
                status = 'stale'
            else:
                status = 'old'
            
            return {
                'driver_id': driver_id,
                'driver_name': current_trip.driver_id.name,
                'driver_phone': getattr(current_trip.driver_id, 'phone_number', '') or getattr(current_trip.driver_id, 'phone', ''),
                'trip_id': current_trip.id,
                'trip_code': current_trip.code or f'Trip-{current_trip.id}',
                'vehicle_name': current_trip.truck_id.name if current_trip.truck_id else 'No Vehicle',
                'vehicle_plate': current_trip.truck_id.license_plate if current_trip.truck_id else '',
                'latitude': latest_checkpoint.latitude,
                'longitude': latest_checkpoint.longitude,
                'last_update': latest_checkpoint.create_date.isoformat(),
                'minutes_ago': minutes_ago,
                'status': status,
                'container_number': getattr(current_trip, 'container_number', '') or '',
                'plan_type': getattr(current_trip, 'plan_type', '') or '',
            }
            
        except Exception as e:
            _logger.error(f"Error getting driver latest location: {str(e)}", exc_info=True)
            return None

    @api.model
    def get_all_active_driver_locations(self):
        """
        Get latest locations for all drivers with current trips
        
        Returns:
            list: Array of driver location data
        """
        try:
            Trip = self.env['trucking_planning.trip']
            Checkpoint = self.env['trucking_planning.trip_checkpoint']
            
            # Get all current trips with their latest checkpoints directly
            current_trips = Trip.search([
                ('is_current', '=', True),
                ('status', 'not in', ['cancelled', 'done']),
                ('driver_id', '!=', False)
            ])
            
            _logger.info(f"Found {len(current_trips)} current trips")
            
            driver_locations = []
            for trip in current_trips:
                # Get latest checkpoint for this trip directly
                latest_checkpoint = Checkpoint.search([
                    ('trip_id', '=', trip.id)
                ], order='create_date desc', limit=1)
                
                if latest_checkpoint:
                    # Calculate time difference
                    now = fields.Datetime.now()
                    time_diff = now - latest_checkpoint.create_date
                    minutes_ago = int(time_diff.total_seconds() / 60)
                    
                    # Determine status based on freshness
                    if minutes_ago <= 30:
                        status = 'fresh'
                    elif minutes_ago <= 60:
                        status = 'stale'
                    else:
                        status = 'old'

                    # Lấy tọa độ Start và Destination
                    start_location = trip.actual_source_location_id
                    dest_location = trip.actual_destination_location_id

                    location_data = {
                        'driver_id': trip.driver_id.id,
                        'driver_name': trip.driver_id.name,
                        'driver_phone': getattr(trip.driver_id, 'phone_number', '') or getattr(trip.driver_id, 'phone', ''),
                        'trip_id': trip.id,
                        'trip_code': trip.code or f'Trip-{trip.id}',
                        'vehicle_name': trip.truck_id.name if trip.truck_id else 'No Vehicle',
                        'vehicle_plate': trip.truck_id.license_plate if trip.truck_id else '',
                        'latitude': latest_checkpoint.latitude,
                        'longitude': latest_checkpoint.longitude,
                        'last_update': latest_checkpoint.create_date.isoformat(),
                        'minutes_ago': minutes_ago,
                        'status': status,
                        'container_number': getattr(trip, 'container_number', '') or '',
                        'plan_type': getattr(trip, 'plan_type', '') or '',
                        # Thêm Start và Destination
                        'start_lat': start_location.latitude if start_location and start_location.latitude else None,
                        'start_lng': start_location.longitude if start_location and start_location.longitude else None,
                        'start_address': start_location.address if start_location and start_location.address else '',
                        'start_contact_phone': start_location.contact_phone if start_location and start_location.contact_phone else '',
                        'start_name': start_location.name if start_location else 'Unknown Start',
                        'dest_lat': dest_location.latitude if dest_location and dest_location.latitude else None,
                        'dest_lng': dest_location.longitude if dest_location and dest_location.longitude else None,
                        'dest_name': dest_location.name if dest_location else 'Unknown Destination',
                        'dest_address': dest_location.address if dest_location and dest_location.address else '',
                        'dest_contact_phone': dest_location.contact_phone if dest_location and dest_location.contact_phone else '',
                    }

                    driver_locations.append(location_data)
                    _logger.info(f"Added location for trip {trip.id}: {location_data['driver_name']} at {location_data['latitude']}, {location_data['longitude']}")
                else:
                    _logger.warning(f"No checkpoints found for trip {trip.id}")
            
            _logger.info(f"Returning {len(driver_locations)} driver locations")
            return driver_locations
            
        except Exception as e:
            _logger.error(f"Error getting all active driver locations: {str(e)}", exc_info=True)
            return []

    @api.model
    def get_trip_route_history(self, trip_id):
        """
        Get all checkpoints for a trip to display route history
        
        Args:
            trip_id: ID of the trip
            
        Returns:
            list: Array of checkpoint data ordered by time
        """
        try:
            Checkpoint = self.env['trucking_planning.trip_checkpoint']
            
            checkpoints = Checkpoint.search([
                ('trip_id', '=', trip_id)
            ], order='create_date asc')
            
            route_points = []
            for checkpoint in checkpoints:
                route_points.append({
                    'checkpoint_id': checkpoint.id,
                    'latitude': checkpoint.latitude,
                    'longitude': checkpoint.longitude,
                    'timestamp': checkpoint.create_date.isoformat(),
                })
            
            return route_points
            
        except Exception as e:
            _logger.error(f"Error getting trip route history: {str(e)}", exc_info=True)
            return []

    @api.model
    def get_tracking_statistics(self):
        """
        Get overall tracking statistics for dashboard
        
        Returns:
            dict: Statistics data
        """
        try:
            Trip = self.env['trucking_planning.trip']
            
            # Get all current trips
            current_trips = Trip.search([
                ('is_current', '=', True),
                ('status', 'not in', ['cancelled', 'done']),
                ('driver_id', '!=', False)
            ])
            
            # Get locations for statistics
            locations = self.get_all_active_driver_locations()
            
            fresh_count = len([loc for loc in locations if loc['status'] == 'fresh'])
            stale_count = len([loc for loc in locations if loc['status'] == 'stale'])
            old_count = len([loc for loc in locations if loc['status'] == 'old'])
            no_location_count = len(current_trips) - len(locations)
            missing_location_count = 0
            for trip in current_trips:
                start_location = trip.actual_source_location_id
                dest_location = trip.actual_destination_location_id

                # Kiểm tra nếu thiếu latitude/longitude ở start hoặc dest
                start_missing = not (start_location and start_location.latitude and start_location.longitude)
                dest_missing = not (dest_location and dest_location.latitude and dest_location.longitude)

                if start_missing or dest_missing:
                    missing_location_count += 1
            return {
                'active_trips': len(current_trips),
                'fresh_locations': fresh_count,
                'stale_locations': stale_count,
                'old_locations': old_count,
                'no_location': no_location_count,
                'missing_location': missing_location_count
            }
            
        except Exception as e:
            _logger.error(f"Error getting tracking statistics: {str(e)}", exc_info=True)
            return {
                'active_trips': 0,
                'fresh_locations': 0,
                'stale_locations': 0,
                'no_location': 0,
                'missing_location': 0
            }

    @api.model
    def create_gps_checkpoint(self, phone, latitude, longitude):
        """
        Create GPS checkpoint for driver based on phone number
        Business logic for processing GPS webhook data
        
        Args:
            phone: Driver's phone number
            latitude: GPS latitude
            longitude: GPS longitude
            
        Returns:
            dict: Success status and created checkpoint info
        """
        try:
            Trip = self.env['trucking_planning.trip']
            Checkpoint = self.env['trucking_planning.trip_checkpoint']
            
            # Find driver by phone (handle different formats)
            # Returns res.partner.driver record
            driver = self._find_driver_by_phone(phone)
            if not driver:
                raise UserError(f"Driver not found for phone number: {phone}")
            
            # Find driver's current trip
            # trip.driver_id is res.partner.driver
            current_trip = Trip.search([
                ('driver_id', '=', driver.id),  # Use res_partner_driver
                ('is_current', '=', True),
                ('status', 'not in', ['cancelled', 'done'])
            ], limit=1)
            
            if not current_trip:
                raise UserError(f"No current trip found for driver {driver.name}")
            
            # Create checkpoint
            checkpoint_data = {
                'trip_id': current_trip.id,
                'longitude': longitude,
                'latitude': latitude,
            }
            
            checkpoint = Checkpoint.create(checkpoint_data)
            
            _logger.info(
                f"GPS checkpoint created via service: "
                f"Checkpoint ID: {checkpoint.id}, Trip: {current_trip.code}, "
                f"Driver: {driver.name}, Location: {latitude}, {longitude}"
            )
            
            return {
                'success': True,
                'checkpoint_id': checkpoint.id,
                'trip_id': current_trip.id,
                'trip_code': current_trip.code or f'Trip-{current_trip.id}',
                'driver_id': driver.id,  # Return res.partner.driver
                'driver_name': driver.name
            }
            
        except UserError as e:
            _logger.warning(f"GPS checkpoint creation failed: {str(e)}")
            raise
        except Exception as e:
            _logger.error(f"Error creating GPS checkpoint: {str(e)}", exc_info=True)
            raise UserError(f"Failed to create GPS checkpoint: {str(e)}")

    @api.model
    def _find_driver_by_phone(self, phone):
        """
        Find driver by phone number, handling different formats (local vs international)
        
        Args:
            phone: Phone number to search for
            
        Returns:
            res.partner.driver record or None
        """
        # Use res.partner.driver model (same as old webhook code)
        Driver = self.env['res.partner.driver']
        
        # Try exact match first (phone field is inherited from res.partner)
        driver = Driver.search([('phone', '=', phone)], limit=1)
        _logger.info(f"Phone lookup for '{phone}': exact match = {'found' if driver else 'not found'}")
        
        if not driver and phone.startswith('84'):
            # Convert international to local: 84965774192 -> 0965774192
            local_phone = '0' + phone[2:]
            driver = Driver.search([('phone', '=', local_phone)], limit=1)
            if driver:
                _logger.info(f"Found driver using local format {local_phone} for international phone {phone}")
            
            # Also try 9-digit format: 84965774192 -> 965774192
            if not driver and len(phone) == 11:  # 84 + 9 digits
                nine_digit_phone = phone[2:]  # Remove '84' prefix
                driver = Driver.search([('phone', '=', nine_digit_phone)], limit=1)
                if driver:
                    _logger.info(f"Found driver using 9-digit format {nine_digit_phone} for international phone {phone}")
        
        elif not driver and phone.startswith('0'):
            # Convert local to international: 0965774192 -> 84965774192
            international_phone = '84' + phone[1:]
            driver = Driver.search([('phone', '=', international_phone)], limit=1)
            if driver:
                _logger.info(f"Found driver using international format {international_phone} for local phone {phone}")
        
        return driver

    @api.model
    def _get_stale_threshold(self):
        """Get the stale threshold from settings (in minutes)"""
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'vehicle_tracking.stale_threshold', default='60'
        ))

