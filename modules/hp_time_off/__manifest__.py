# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HP Time Off',
    'version': '1.0',
    'author': 'HPL',
    'category': 'HP',
    "license": "LGPL-3",
    'description': """
HP Time Off App
===================================================
""",
    'depends': ['hp_employee', 'hr_holidays'],
    'data': [
        # data demo
        'data/demo_data.xml',

        # views
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
