# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HP Time Off',
    'version': '1.0',
    'author': 'HPL',
    'category': 'HP',
    "license": "LGPL-3",
    'description': """
HP Employee App
===================================================
""",
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_leave_type_views.xml',
        'views/hr_leave_views.xml',
    ],
    "assets": {
        "web.assets_backend": [
           
        ]
    },
    'installable': True,
    'application': True,
}
