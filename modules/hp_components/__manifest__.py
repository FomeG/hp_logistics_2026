# -*- coding: utf-8 -*-
{
    'name': 'hp_components',
    'description': 'provide service components',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    "license": "LGPL-3",
    'depends': ['base','project','sale','mail','component','component_event', 'queue_job'],
    'data': [
        'security/ir.model.access.csv',
        'data/partner_main_type_data.xml',
        'data/department_type_demo.xml',
        'data/container_type_data.xml',
        'data/shipping_line_data.xml',
        'data/region_data.xml',
        'data/country_region_data.xml',
        'data/port_data.xml',
        'views/location_base_views.xml',
        'views/route_base_views.xml',
        'views/container_type_views.xml',
        'views/shipping_line_views.xml',
        'views/wizards/import_shipping_line_wizard.xml',
        'views/wizards/import_route_base_wizard.xml',
        'views/hp_menu.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'hp_components/static/src/js/many2one_new_tab.js',
        ],
    },
    'installable': True,
    'application': True,
}

