# -*- coding: utf-8 -*-
{
    'name': 'HP Vehicle Tracking',
    'version': '1.0.0',
    'category': 'Operations',
    'summary': 'Real-time vehicle location tracking with GPS checkpoints',
    'description': """
        Vehicle Tracking System
        =======================
        
        Features:
        ---------
        * Real-time vehicle location tracking on map
        * GPS checkpoint integration via Zalo webhook
        * OpenStreetMap integration with Leaflet.js
        * Driver location monitoring
        * Auto-refresh map display
        * Color-coded location freshness indicators
        
        This module provides a comprehensive vehicle tracking solution
        integrated with the HP Trucking Planning system.
    """,
    'author': 'HP Logistics',
    'website': 'https://www.hplogistics.com',
    'depends': [
        'base',
        'web',
        'hp_trucking_planning',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/vehicle_tracking_map_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

