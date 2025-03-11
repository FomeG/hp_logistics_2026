# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HP Employees',
    'version': '1.0',
    'category': 'Hidden',
    "license": "LGPL-3",
    'description': """
HP Employee App
===================================================
""",
    'depends': ['base', 'hr'],
    'data': [
        'views/hr_employee_action_views.xml',
        'views/hr_employee_form_views.xml',
    ],
    "assets": {
        "web.assets_backend": [

        ]
    },
    'installable': True,
    'application': False,
}
