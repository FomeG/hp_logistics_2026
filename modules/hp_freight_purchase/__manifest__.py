# -*- coding: utf-8 -*-
{
    'name': 'hp_freight_purchase',
    'description': 'This module is used by pricing team',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    "license": "LGPL-3",
    'depends': ['base', 'mail', 'sale','hp_components'],
    'data': [
        # security
        'security/hp_freight_purchase_security.xml',
        'security/ir.model.access.csv',

        #views
        'views/freight_purchase_region_views.xml',
        'views/freight_purchase_fee_views.xml',
        'views/freight_purchase_port_views.xml',
        'views/freight_purchase_route_views.xml',
        'views/freight_purchase_vessel_views.xml',
        'views/freight_purchase_container_type_views.xml',
        'views/freight_purchase_quotation_views.xml',
        'views/freight_purchase_booking_views.xml',

        #menu
        'views/freight_purchase_menus.xml',
    ],
    'installable': True,
    'application': True,
}

