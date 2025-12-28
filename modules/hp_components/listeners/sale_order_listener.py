from odoo.addons.component.core import Component
from ..models import constants


import logging
_logger = logging.getLogger(__name__)

class SaleOrderListener(Component):
    _name = 'custom_component.sale_order_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']


    def on_record_write(self, record, fields=None):
        # _logger.info("SaleOrderListener triggered on_record_write with fields: %s, record: %s", fields, record)
        # if record.is_activated() and not self.env.context.get('skip_price_request_listener'):
        #     record.with_delay()._handle_quotation_activated()
        # elif record.is_cancelled():
        #     record.with_delay()._handle_quotation_cancelled()
        # elif record.is_customer_confirmed():
        #     record.with_delay()._handle_quotation_customer_confirmed()
        # elif record.is_sale_leader_confirmed():
        #     record.with_delay()._handle_quotation_sale_leader_confirmed()
        # elif record.is_order():
        #     record.with_delay()._handle_quotation_confirmed()
        if 'state' in fields:
            state = record.state
            match state:            
                case constants.SaleOrderState.SENT_TO_CLIENT:
                    # todo
                    return

                case constants.SaleOrderState.REVIEW:
                    # todo
                    return
                    
                case constants.SaleOrderState.SENT_TO_LEADER:
                    # todo
                    return
                    
                case constants.SaleOrderState.SALE:
                    # todo
                    return
                
                case _:
                    return