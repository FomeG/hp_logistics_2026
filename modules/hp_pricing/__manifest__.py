# Copyright 2025
{
    'name': 'HP Pricing',
    'description': "HP Pricing",
    'version': '1.0',
    'sequence': 1,
    'author': 'NgocVu',
    'license': 'Other proprietary',
    'category': 'HP/HP Logistic',
    'images': [],
    'depends': [
        'mail', 'base', 'sale', 'product', 'sale_management',
    ],
    'data': [
        # security
        'security/hp_pricing_security.xml',
        'security/ir.model.access.csv',
        
        #views
        'views/pricing_pol_views.xml',
        'views/pricing_pod_views.xml',
        'views/pricing_region_views.xml',
        'views/pricing_shipping_line.xml',
        'views/pricing_shipping_vessel.xml',
        'views/pricing_sealine_views.xml',

        'views/pricing_voyage_views.xml',
        'views/pricing_booking_views.xml',

        'views/pricing_team_views.xml',
        'views/pricing_team_member_views.xml',
        'views/product_template_views.xml',

        'views/pricing_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
