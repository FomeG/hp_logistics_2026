{
    'name': 'HP AI Base',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Base module for AI integration - supports OpenAI and Anthropic',
    'description': """
        HP AI Base Module
        =================
        This module provides:
        - AI Provider configuration (OpenAI, Anthropic)
        - AI Bot user for chatter integration
        - Prompt template management
        - Core AI service for API calls
        - Usage logging and cost tracking
    """,
    'author': 'HP Logistics',
    'website': 'https://hplogistics.vn',
    'depends': ['base', 'mail'],
    'data': [
        'security/hp_ai_base_security.xml',
        'security/ir.model.access.csv',
        'data/ai_bot_data.xml',
        'data/ai_provider_data.xml',
        # ai_usage_log_views.xml must be loaded before ai_provider_views.xml
        # because ai_provider_views.xml references action_ai_usage_log
        'views/ai_usage_log_views.xml',
        'views/ai_provider_views.xml',
        'views/ai_prompt_template_views.xml',
        'views/res_config_settings_views.xml',
        'views/hp_ai_base_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
