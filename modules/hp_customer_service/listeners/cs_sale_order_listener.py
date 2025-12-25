from odoo.addons.component.core import Component
from odoo.addons.hp_components.models import constants


class CsSalesOrderListener(Component):
    _name = 'cs.sale.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']

    def on_record_write(self, record, fields=None):
        if not fields or 'state' not in fields:
            return
        
        if self._can_send_sale_order_to_cs(record):
            self.env['cs.order'].create_from_sale_order(record)


    # def _can_send_sale_order_to_cs(self, sale_order):
        # if sale_order._origin.state != constants.SaleOrderState.SALE and sale_order.state == constants.SaleOrderState.SALE:
            # return True
        # return False

        
    def _can_send_sale_order_to_cs(self, sale_order):
        old_state = sale_order.env.context.get('old_state')
        new_state = sale_order.state
        
        if old_state != constants.SaleOrderState.SALE and new_state == constants.SaleOrderState.SALE:
            return True
        return False

