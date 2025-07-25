# -*- coding: utf-8 -*-
{
    'name': "hp_document",
    'summary': 'Shared document library for bookings, quotations, sales',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    'depends': ['base','hp_freight_purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/hp_document_booking_document_views.xml',
        'views/hp_document_views.xml',
        # data
        'data/cron_job.xml',
        'data/data_config.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hp_document/static/src/js/file_preview_client_action.js',
            'hp_document/static/src/xml/file_preview_template.xml',
        ],
    },
    'installable': True,
    'application': True,
}

