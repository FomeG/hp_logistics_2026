# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HP Employees',
    'version': '1.0',
    'author': 'HPL',
    'category': 'HP',
    "license": "LGPL-3",
    'description': """
HP Employee App
===================================================
""",
    'depends': ['base', 'hr','hr_org_chart'],
    'data': [
        # 'data/demo_data.xml',
        'views/hidden_btn_new_views.xml',
        'views/hr_department_form_views.xml',
        'views/hr_employee_form_views.xml',
    ],
    "assets": {
        "web.assets_backend": [
            'hp_employee/static/src/js/hide_action_create.js',
        ]
    },
    # 'demo': [
    #     'data/demo_data.xml',
    # ],
    'installable': True,
    'application': False,
}
