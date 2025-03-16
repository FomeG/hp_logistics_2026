# Copyright 2025
{
    'name': 'HP Sale',
    'description': "HP Sale",
    'version': '1.0',
    'sequence': 1,
    'author': 'NgocVu',
    'license': 'Other proprietary',
    'category': 'HP/HP Logistic',
    'images': [],
    'depends': [
        'mail', 'base', 'sale', 'product', 'sale_management', 'account'
    ],
    'data': [
        # data
        'data/product_category.xml',
        'data/product_data.xml',
        'data/price_category_cron.xml',

        # security
        'security/hp_sale_security.xml',
        'security/ir.model.access.csv',
        
        #views
        'views/product_template_views.xml',
        'views/price_category_views.xml',
        'views/product_category_views.xml',

        'views/pricing/pricing_pol_views.xml',
        'views/pricing/pricing_pod_views.xml',
        'views/pricing/pricing_region_views.xml',
        'views/pricing/pricing_shipping_line.xml',
        'views/pricing/pricing_shipping_vessel.xml',

        'views/pricing/pricing_voyage_views.xml',
        'views/pricing/pricing_booking_views.xml',

        'views/pricing/pricing_team_views.xml',
        'views/pricing/pricing_team_member_views.xml',

        'views/trucking/trucking_team_views.xml',
        'views/trucking/trucking_team_member_views.xml',

        'views/sale_menus.xml',

    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'hp_sale/static/src/js/hide_add_properties.js',
            'hp_sale/static/src/js/hide_action_delete.js',
            'hp_sale/static/src/xml/hide_chatter_actions.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
