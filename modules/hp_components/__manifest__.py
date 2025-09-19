# -*- coding: utf-8 -*-
{
    'name': 'hp_components',
    'description': 'provide service components',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    "license": "LGPL-3",
    'depends': ['base','project','sale','mail','component','component_event', 'queue_job'],
    'data': [
        'data/partner_main_type_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hp_components/static/src/js/many2one_new_tab.js',
        ],
    },
    'installable': True,
    'application': False,
}

