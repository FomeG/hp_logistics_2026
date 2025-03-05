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
        'mail', 'base', 'sale', 'product', 'sale_management',
    ],
    'data': [
        # data
        'data/product_data.xml',
        'data/product_data.xml',
        'data/price_category_cron.xml',

        # security
        'security/hp_sale_security.xml',
        'security/ir.model.access.csv',
        
        #views
        'views/product_template_views.xml',
        'views/price_category_views.xml',
        'views/product_category_views.xml'

        'views/menus.xml',

    ],
    'demo': [],
    'installable': True,
}
