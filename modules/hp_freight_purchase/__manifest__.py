# -*- coding: utf-8 -*-
{
    'name': 'hp_freight_purchase',
    'description': 'This module is used by pricing team',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    "license": "LGPL-3",
    'depends': ['base', 'mail', 'sale','hp_components', 'hp_sale'],
    'data': [
        #data demo
        'demo/container_type_demo.xml',
        'demo/fee_demo.xml',
        'demo/region_demo.xml',
        'demo/port_demo.xml',
        'demo/shipping_line_demo.xml',
        'demo/vessels_demo.xml',

        # security
        'security/hp_freight_purchase_security.xml',
        'security/ir.model.access.csv',

        #views
        'views/freight_purchase_region_views.xml',
        'views/freight_purchase_fee_views.xml',
        'views/freight_purchase_port_views.xml',
        'views/freight_purchase_route_views.xml',
        'views/freight_purchase_vessel_views.xml',
        'views/freight_purchase_shipping_line_views.xml',
        'views/freight_purchase_container_type_views.xml',
        'views/freight_purchase_quotation_views.xml',
        'views/freight_purchase_quotation_line_views.xml',
        'views/freight_purchase_booking_views.xml',
        'views/freight_purchase_booking_line_views.xml',
        'views/sale_order_line_selection_views.xml',


        #menu
        'views/freight_purchase_menus.xml',
    ],
    # 'demo': [
    #     'demo/container_type_demo.xml',
    #     'demo/fee_demo.xml',
    #     'demo/port_demo.xml',
    #     'demo/region_demo.xml',
    #     'demo/shipping_line_demo.xml',
    #     'demo/vessels_demo.xml',
    # ],
    'assets': {
        'web.assets_backend': [
            'hp_freight_purchase/static/src/js/many2one_new_tab.js',
        ],
    },
    'installable': True,
    'application': True,
}

