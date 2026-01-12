from odoo.addons.component.core import Component
from ...hp_components.models import constants

class SaleOrderListener(Component):
    _name = 'sale.order.line.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order.line']

    def on_record_create(self, record, fields=None):
        if record.order_id.state == constants.SaleOrderState.DRAFT:
            record.order_id.write({'state': constants.SaleOrderState.ACTIVE})
        return
