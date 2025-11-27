from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
from ...hp_components.models import constants
import logging


class SaleOrderInherrit(models.Model):
    _inherit = 'sale.order'

    def select_truck_freight(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Normal Product',
            'res_model': 'product.template',
            'view_mode': 'list,search',
            'views': [
                (self.env.ref('hp_sale.product_template_normal_list_view').id, 'list'),
                (self.env.ref('hp_sale.product_template_normal_search_view').id, 'search'),
            ],
            'target': 'new',
            'domain': [
                ('route_id', '!=', False),
                ('product_type', '=', constants.ProductTemplateType.TRUCK_FREIGHT),
                ('categ_id.service_type', '=', self.service_type),
            ],
            'context': {
                'sale_order_id': self.id,
                'dialog_size': 'extra-large',
                'is_truck_freight': True,
                'create': False,
                'select_mode': True,
                'group_by': 'categ_id',
            },
        }

