from odoo.addons.component.core import Component
from odoo.addons.hp_components.models import constants


class CsSalesOrderListener(Component):
    _name = 'cs.sale.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']

    def on_record_write(self, record, fields=None):
        if self._can_send_sale_order_to_cs(record):
            self.env['cs.order'].create_from_sale_order(record)


    def _can_send_sale_order_to_cs(self, sale_order):
        if sale_order._origin.state != constants.SaleOrderState.DONE and sale_order.state == constants.SaleOrderState.DONE:
            return True
        return False