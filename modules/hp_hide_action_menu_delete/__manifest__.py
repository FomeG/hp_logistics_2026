{
    'name': 'HP Hide Action Delete Button',
    'version': '1.0',
    'category': 'Hidden',
    "license": "LGPL-3",
    'description': """
HP Hide Action Delete Button
===================================================
""",
    'depends': ['base'],
    'data': [
        'views/inherit_res_users_view.xml',
    ],
    "assets": {
        "web.assets_backend": [
            'hp_hide_action_menu_delete/static/src/**/*',
        ]
    },
    'installable': True,
    'application': False,
}                  