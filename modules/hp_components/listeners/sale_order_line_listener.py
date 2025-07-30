from odoo.addons.component.core import Component
from odoo import exceptions

import logging
_logger = logging.getLogger(__name__)

class SaleOrderListener(Component):
    _name = 'custom_component.sale_order_line_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order.line']


    def on_record_write(self, record, fields=None):
        if not record.active and record.order_id.state == 'pricing_leader_confirm' and record.booking_line_id:
            record.booking_line_id.sudo().write({
                'status': 'cancelled',
            })
