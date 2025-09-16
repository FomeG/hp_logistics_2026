# -*- coding: utf-8 -*-
{
    'name': "hp_customer_service",
    'summary': "Short (1 phrase/line) summary of the module's purpose",
    'description': 'This module is used by CS team',
    'author': 'HPL',
    'category': 'HP',
    'version': '0.1',

    'depends': ['base','hp_components'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/cs_job_views.xml',
        'views/cs_menus.xml',
        'report/HBL_template.xml',
        'report/ir_actions_report.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}

