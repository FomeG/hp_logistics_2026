from odoo.addons.component.core import Component
from ...hp_components.models import constants

class SaleOrderListener(Component):
    _name = 'sale.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']

    def on_record_create(self, record, fields=None):
        if record.order_line and record.state == constants.SaleOrderState.DRAFT:
            record.write({'state': constants.SaleOrderState.ACTIVE})
        return
