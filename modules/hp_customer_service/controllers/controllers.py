# -*- coding: utf-8 -*-
# from odoo import http


# class HpCustomerService(http.Controller):
#     @http.route('/hp_customer_service/hp_customer_service', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hp_customer_service/hp_customer_service/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hp_customer_service.listing', {
#             'root': '/hp_customer_service/hp_customer_service',
#             'objects': http.request.env['hp_customer_service.hp_customer_service'].search([]),
#         })

#     @http.route('/hp_customer_service/hp_customer_service/objects/<model("hp_customer_service.hp_customer_service"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hp_customer_service.object', {
#             'object': obj
#         })

