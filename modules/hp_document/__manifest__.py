# -*- coding: utf-8 -*-
{
    'name': "hp_document",
    'summary': 'Shared document library for bookings, quotations, sales',
    'author': 'HPL',
    'category': 'HP',
    'version': '18.0.0.0.1',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/hp_document_booking_document_views.xml',
        'views/hp_document_views.xml',
        # data
        'data/cron_job.xml',
        'data/data_config.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hp_document/static/src/js/attachment_preview.js',
            'hp_document/static/src/xml/attachment_preview.xml',
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.css',
            'https://cdn.jsdelivr.net/npm/@fancyapps/fancybox@3.5.6/dist/jquery.fancybox.min.js'
        ],
    },
    'installable': True,
    'application': True,
}

