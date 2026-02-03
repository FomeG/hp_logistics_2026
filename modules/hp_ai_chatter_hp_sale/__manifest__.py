{
    'name': 'HP AI Chatter - Sale Integration',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'AI Assistant integration for HP Sale module',
    'description': """
        HP AI Chatter - Sale Integration
        =================================
        This module adds "Ask AI" server actions to HP Sale models:
        - Sale Orders / Quotations
        - Sea Freight Requests
    """,
    'author': 'HP Logistics',
    'website': 'https://hplogistics.vn',
    'depends': ['hp_ai_chatter', 'hp_sale'],
    'data': [
        'data/ai_server_actions.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
