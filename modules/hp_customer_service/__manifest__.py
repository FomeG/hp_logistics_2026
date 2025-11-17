# -*- coding: utf-8 -*-
{
    'name': "hp_customer_service",
    'summary': "This module is to manage job that will be delivered to other teams",
    'description': 'This module is used by CS team',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    "license": "LGPL-3",
    # any module necessary for this one to work correctly
    'depends': ['hp_freight_purchase', 'hp_trucking_planning'],
    # always loaded
    'data': [
        'security/hp_customer_service_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_cs_batch_order_data.xml',
        'data/ir_sequence_cs_order_data.xml',
        'wizard/hp_bank_wizard_view.xml',
        'views/cs_batch_order_views.xml',
        'views/cs_bill_lading_views.xml',
        'views/cs_booking_views.xml',
        'views/cs_container_views.xml',
        'views/cs_order_views.xml',
        'views/cs_pre_alert_views.xml',
        'views/cs_shipping_instruction_views.xml',
        'views/cs_task_views.xml',
        'views/cs_menus.xml',
        # 'report/HBL_template.xml',
        # 'report/debit_template.xml',
        # 'report/ir_actions_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'data/bank_demo_data.xml',
    ],
    'installable': True,
    'application': True,
}

