# -*- coding: utf-8 -*-
{
    'name': "hp_trucking_planning",
    'summary': "This module allows to manage driver, truck, cost and make planning, order for transport",
    'description': "This module allows to manage driver, truck, cost and make planning, order for transport",
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.2',
    "license": "LGPL-3",
    'depends': ['base','hp_components', 'queue_job', 'portal','hp_employee'],
    'data': [
        'security/hp_trucking_planning_security.xml',
        'security/ir.model.access.csv',
        'data/trucking_planning_sequences.xml',
        #wizards
        'views/wizards/import_client_wizard.xml',
        'views/wizards/import_vehicle_driver_wizard.xml',
        'views/wizards/import_route_wizard.xml',

        'views/trucking_planning_shipping_line_views.xml',
        'views/trucking_planning_vehicle_views.xml',
        'views/trucking_planning_client_views.xml',
        'views/trucking_planning_location_views.xml',
        'views/trucking_planning_route_views.xml',
        'views/trucking_planning_driver_views.xml',
        'views/trucking_planning_plan_views.xml',
        'views/trucking_planning_plan_line_views.xml',
        'views/trucking_planning_branch_views.xml',
        'views/trucking_planning_trip_views.xml',
        'views/trucking_planning_menu.xml',
        'views/trucking_planning_portal_templates.xml',
        'report/ir_actions_report.xml',
        'report/trip_order_templates.xml',
    ],
    'installable': True,
    'application': True,
}

