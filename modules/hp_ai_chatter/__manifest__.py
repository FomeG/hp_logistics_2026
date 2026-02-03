{
    'name': 'HP AI Chatter',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'AI Assistant integration with Odoo Chatter',
    'description': """
        HP AI Chatter Module
        ====================
        This module provides:
        - AI Bot that responds to messages in chatter
        - Mention @AI Assistant to get AI responses
        - Context-aware AI that understands the current record
        - Conversation history within chatter thread
        - "Ask AI" in Action menu for form views
    """,
    'author': 'HP Logistics',
    'website': 'https://hplogistics.vn',
    'depends': ['hp_ai_base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_chatter_data.xml',
        'data/ai_server_actions.xml',
        'views/ai_chatter_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hp_ai_chatter/static/src/js/ai_chatter.js',
            'hp_ai_chatter/static/src/xml/ai_chatter_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
