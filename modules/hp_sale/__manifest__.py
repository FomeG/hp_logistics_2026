# Copyright 2025
{
    'name': 'HP Sale',
    'description': "HP Sale",
    'version': '1.0',
    'sequence': 1,
    'author': 'NgocVu',
    'license': 'Other proprietary',
    'category': 'HP/HP Logistic',
    'images': [],
    'depends': [
        'product', 'account','hp_employee'
    ],
    'data': [
        # data
        'data/product_category.xml',
        'data/product_data.xml',
        'data/pricelist_data.xml',
        'data/demo_selling_week_data.xml',
        'data/demo_product_template_data.xml',
        'data/demo_product_selling_week_data.xml',
        'data/demo_client_data.xml',
        'data/demo_quotations_data.xml',
        #'data/price_category_cron.xml',
        'data/selling_week_state_cron.xml',

        # wizards
        'views/wizards/import_client_wizard.xml',
        'views/wizards/mass_assign_sale_client_wizard.xml',

        # security
        'security/hp_sale_security.xml',
        'security/ir.model.access.csv',
        
        #views
        'views/product_template_views.xml',
        'views/res_config_settings.xml',
        # 'views/price_category_views.xml',
        'views/product_category_views.xml',
        'views/change_menu_customer_views.xml',
        # 'views/inherit_form_create_customer_views.xml',
        'views/sale_order_inherit.xml',
        # 'views/pricing_booking_form_views_inherit.xml',
        'views/res_partner_client_views.xml',
        'views/selling_week_views.xml',
        'views/product_template_selling_week_views.xml',
        'views/product_template_selling_week_line_views.xml',
        'views/sale_configuaration_views.xml',
        'views/product_template_normal_list_views.xml',
        'views/sale_menus.xml',
        'report/ir_actions_report.xml',
        'report/report_quotation_template.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'hp_sale/static/src/js/hide_add_properties.js',
            'hp_sale/static/src/js/hide_action_delete.js',
            'hp_sale/static/src/xml/hide_chatter_actions.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
