# Copyright 2025
{
    'name': 'HP Trucking',
    'description': "HP Trucking",
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
        'security/hp_trucking_security.xml',
        'security/ir.model.access.csv',
        
        #views
        'views/trucking_team_views.xml',
        'views/trucking_team_member_views.xml',
        'views/product_template_views.xml',
        'views/trucking_pod_views.xml',
        'views/trucking_pol_views.xml',
        'views/trucking_roadline_views.xml',

        'views/trucking_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
