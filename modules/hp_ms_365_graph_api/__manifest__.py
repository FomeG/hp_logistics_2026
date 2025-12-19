# -*- coding: utf-8 -*-
{
    'name': "hp_ms_365_graph_api",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Nguyễn Đức Hải Anh",
    'license': 'LGPL-3',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HP',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],  # nếu dùng mail.mail hoặc mail.message

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ms_user_view.xml',
        'data/cron_job.xml',
        'views/mail_message_view.xml',
        'views/ir_attachment_views.xml',
        'views/menu.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

