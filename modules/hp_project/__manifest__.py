# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HP Project',
    'version': '1.0',
    'category': 'HP',
    'description': """
HP Project App
===================================================
""",
    'depends': ['base', 'web', 'mail', 'bus', 'project', 'sale', 'sale_project', 'sales_team', 'hp_freight_purchase', 'hp_sale', 'hp_components'],
    'data': [
        #data
        'data/project_default.xml',

        #security
        # 'security/ir.model.access.csv',

        #view
        'views/project_task_form_views.xml',
        'views/project_task_list_views.xml',

    ],
    'assets': {
        'web.assets_backend': [

        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
