from itertools import count

from odoo.addons.component.core import Component
from odoo.addons.sale.models.sale_order import SaleOrder
from ..services.task_service import TaskService

import logging
_logger = logging.getLogger(__name__)

class SaleOrderListener(Component):
    _name = 'custom_component.sale_order_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']


    def on_record_write(self, record, fields=None):
        _logger.info("SaleOrderListener triggered on_record_write with fields: %s, record: %s", fields, record)
        if record.is_activated():
            #todo: check old status != activated
            _logger.info("Creating price request task")
            self._handle_quotation_activated(record)
        elif record.is_cancelled():
            self._handle_quotation_cancelled(record)
        elif record.is_customer_confirmed():
            self._handle_quotation_customer_confirmed(record)
        elif record.is_sale_leader_confirmed():
            self._handle_quotation_sale_leader_confirmed(record)

    def _handle_quotation_activated(self,record: SaleOrder) -> None:
        project = False
        service = TaskService(self.env)
        sale_order_lines_without_price = record.get_sale_order_lines_missing_price()
        _logger.info(f"sale_order_lines_without_price: {sale_order_lines_without_price}")
        if not sale_order_lines_without_price:
            return
        else:
            # case 1: request price if needed
            project = service.get_project_by_type(TaskService.PROJECT_TYPE_PRICE_REQUEST)
        _logger.info(f"project: {project}")
        if not project:
            return
        for sale_order_line in sale_order_lines_without_price:
            service.create_task_by_sale_order_line('pricing',project.id, TaskService.TASK_TYPE_PRICE_REQUEST, sale_order_line)

    def _handle_quotation_cancelled(self,record: SaleOrder) -> None:
        if record.is_cancelled():
            TaskService(self.env).cancel_tasks_by_sale_order(record)

    def _handle_quotation_customer_confirmed(self,record: SaleOrder) -> None:
        _logger.info("_handle_quotation_customer_confirmed {record}")
        service = TaskService(self.env)
        project = service.get_project_by_type(TaskService.PROJECT_TYPE_APPROVE_QUOTATION)
        if not project:
            return
        service.create_task_by_sale_order('sale', project.id, TaskService.TASK_TYPE_APPROVE_QUOTATION, record)

    def _handle_quotation_sale_leader_confirmed(self,record: SaleOrder) -> None:
        _logger.info("_handle_quotation_sale_leader_confirmed {record}")
        service = TaskService(self.env)
        project = service.get_project_by_type(TaskService.PROJECT_TYPE_APPROVE_QUOTATION)
        if not project:
            return
        service.create_task_by_sale_order('pricing', project.id, TaskService.TASK_TYPE_APPROVE_QUOTATION, record)
