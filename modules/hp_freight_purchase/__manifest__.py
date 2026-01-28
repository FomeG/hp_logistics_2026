# -*- coding: utf-8 -*-
{
    'name': 'hp_freight_purchase',
    'description': 'This module is used by pricing team',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    "license": "LGPL-3",
    'depends': ['hp_sale'],
    'data': [
        # security
        'security/hp_freight_purchase_security.xml',
        'security/ir.model.access.csv',

        #data - must be loaded first
        'data/department_data.xml',
        'demo/vessels_demo.xml',
        # 'data/demo_quotation_data.xml',
        'data/demo_booking_data.xml',
        'data/demo_pricing_hn_data.xml',
        'data/demo_pricing_hcm_data.xml',
        'data/demo_sea_freight_request_data.xml',
        'data/partner_main_type_data.xml',
        'data/freight_purchase_booking_sequences.xml',
        'data/freight_purchase_data_config.xml',
        #data demo
        # 'demo/container_type_demo.xml',
        #'demo/fee_demo.xml',
        #'demo/region_demo.xml',
        # 'demo/port_demo.xml',
        # 'demo/shipping_line_demo.xml',
        'demo/freight_purchase_fee_type_demo.xml',

        #views
        'views/freight_purchase_region_views.xml',
        'views/freight_purchase_fee_views.xml',
        'views/freight_purchase_fee_line_views.xml',
        'views/freight_purchase_fee_type_views.xml',
        'views/freight_purchase_port_views.xml',
        # 'views/freight_purchase_route_views.xml',
        'views/freight_purchase_vessel_views.xml',
        'views/freight_purchase_shipping_line_views.xml',
        'views/freight_purchase_container_type_views.xml',
        # 'views/freight_purchase_quotation_views.xml',
        # 'views/freight_purchase_quotation_line_views.xml',
        'views/freight_purchase_booking_views.xml',
        'views/freight_purchase_booking_line_views.xml',
        'views/freight_purchase_booking_document_views.xml',
        'views/freight_purchase_remind_views.xml',
        'views/hr_team_freight_purchase_views.xml',
#        'views/sale_order_line_selection_views.xml',
#        'views/sale_order_inherit_views.xml',
        'views/sale_order_inherit_views_2.xml',
        'views/res_country_views.xml',
        'views/freight_purchase_assign_booking_views.xml',
        'views/sea_freight_request_inherit_views.xml',
        # wizard views
        'views/wizards/freight_purchase_port_route_request.xml',
        'views/wizards/import_shipping_line_wizard.xml',
        'views/wizards/assign_booking_wizard_views.xml',

        #menu
        'views/freight_purchase_menus.xml',

        #data
        'data/cron_job.xml',
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
        'web.assets_backend': [],
    },
    'installable': True,
    'application': True
}

