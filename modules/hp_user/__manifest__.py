# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HP users',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
HP User App
===================================================
""",
    'depends': ['base'],
    'data': [
        'security/hp_user_security.xml',
        'security/ir.model.access.csv',
        'views/hp_user_menus.xml',
        'data/hp_user_data.xml',
    ],
    'installable': True,
    'application': False,
}
