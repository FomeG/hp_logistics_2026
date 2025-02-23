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
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/hp_user_security.xml',
        'security/ir.model.access.csv',
        'security/position_security.xml',
        'security/res_partner_rules.xml',
        'views/hp_user_menus.xml',
        'views/res_users_view.xml',
        'data/hp_user_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hp_user/static/src/xml/hide_chatter_actions.xml',
        ],
    },
    'installable': True,
    'application': False,
}
