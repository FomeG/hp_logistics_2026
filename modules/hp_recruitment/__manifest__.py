# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HP Recruitment',
    'version': '1.0',
    'author': 'HPL',
    'category': 'HP',
    "license": "LGPL-3",
    'description': """
HP Employee App
===================================================
""",
    'depends': ['hr_recruitment'],
    'data': [
        'views/hr_applicant_views.xml',
    ],
    "assets": {
        "web.assets_backend": [

        ]
    },
    'installable': True,
    'application': False,
}
