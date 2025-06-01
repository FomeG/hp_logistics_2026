
import logging

_logger = logging.getLogger(__name__)

class SaleOrderService:
    _name = "Sale Order Service"
    def __init__(self, env):
        self.env = env

    def update_sale_order_line_price_by_task(self, project_task) -> None:
        sale_order = project_task.sale_order()
        if sale_order.can_update_price():
            #todo get the right price
            project_task.sale_line_id.write({'price_unit': 30})
        else:
            _logger.warning("Cannot update price. Order is not editable.")
