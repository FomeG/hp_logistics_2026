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
    'depends': ['hp_components'],
    'data': [
        # security
        'security/ir.model.access.csv',
        'data/demo_branch_data.xml',
        'data/demo_sale_hn_data.xml',
        'data/demo_sale_hcm_data.xml',
        'data/demo_team_data.xml',
        'views/cs_department_type_views.xml',
        'views/hidden_btn_new_views.xml',
        'views/hr_department_form_views.xml',
        'views/hr_employee_form_views.xml',
        'views/cs_department_type_views.xml',
        'views/hr_branch_views.xml',
        'views/hr_team_views.xml',
        'views/menu.xml',

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
    'application': True,
}
