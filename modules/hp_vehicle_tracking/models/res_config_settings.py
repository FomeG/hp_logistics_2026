# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Map configuration settings
    vehicle_tracking_auto_refresh_interval = fields.Integer(
        string='Auto-refresh Interval (seconds)',
        default=30,
        config_parameter='vehicle_tracking.auto_refresh_interval',
        help='How often the map should auto-refresh to show latest locations (in seconds)'
    )
    
    vehicle_tracking_stale_threshold = fields.Integer(
        string='Stale Location Threshold (minutes)',
        default=60,
        config_parameter='vehicle_tracking.stale_threshold',
        help='Consider location as stale if not updated within this many minutes'
    )
    
    vehicle_tracking_default_map_center_lat = fields.Float(
        string='Default Map Center (Latitude)',
        default=21.0285,
        config_parameter='vehicle_tracking.default_map_center_lat',
        help='Default latitude for map center (e.g., Hanoi: 21.0285)'
    )
    
    vehicle_tracking_default_map_center_lng = fields.Float(
        string='Default Map Center (Longitude)',
        default=105.8542,
        config_parameter='vehicle_tracking.default_map_center_lng',
        help='Default longitude for map center (e.g., Hanoi: 105.8542)'
    )
    
    vehicle_tracking_default_zoom_level = fields.Integer(
        string='Default Zoom Level',
        default=10,
        config_parameter='vehicle_tracking.default_zoom_level',
        help='Default zoom level for the map (1-19, where higher = more zoomed in)'
    )


