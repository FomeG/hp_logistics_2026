# -*- coding: utf-8 -*-
{
    'name': "hp_trucking_planning",
    'summary': "This module allows to manage driver, truck, cost and make planning, order for transport",
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    "license": "LGPL-3",
    'depends': ['base','hp_components'],
    'data': [
        'security/ir.model.access.csv',

        'views/trucking_planning_shipping_line_views.xml',
        'views/trucking_planning_vehicle_views.xml',
        'views/trucking_planning_client_views.xml',
        'views/trucking_planning_location_views.xml',
        'views/trucking_planning_route_views.xml',
        'views/trucking_planning_driver_views.xml',
        'views/trucking_planning_plan_views.xml',
        'views/trucking_planning_menu.xml',
    ],
    'installable': True,
    'application': True,
}

