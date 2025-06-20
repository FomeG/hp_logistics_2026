{
    'name': 'Hide Any Menu User Wise',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Hide Menu, Odoo18 Hide Menu, Hide Menu Odoo, Restrict Menu Items, Odoo18 Menu, Odoo18, Odoo Apps',
    'description': 'Hide Any Menu Item User Wise, Hide Menu Items, Hide Menu',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'views/res_users_views.xml',
        # 'data/menu_items_hide.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}