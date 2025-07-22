from odoo import _, exceptions
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

    def hande_customer_confirm(self, sale_order):
        pricing_lines_without_price = sale_order.order_line.filtered(
            lambda line: line.product_type_filter == 'pricing' and not line.freight_quotation_id
        )

        if pricing_lines_without_price:
            product_names = ", ".join(line.product_id.name for line in pricing_lines_without_price)
            raise exceptions.ValidationError(_(
                "Cannot proceed to customer confirmation. The following products need a pricing quotation assignment: %s"
            ) % product_names)

        for line in sale_order.order_line:
            if line.price_unit < line.base_price:
                raise exceptions.ValidationError(_(
                    "The Price unit can not less than Base price"
                ))

        # Set state to customer_confirm
        sale_order.write({'state': 'customer_confirm'})
        return True