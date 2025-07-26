from itertools import count

from odoo import fields
from odoo.addons.component.core import Component
from odoo.addons.sale.models.sale_order import SaleOrder
from ..services.request_price_service import RequestPriceService
from ..services.project_service import ProjectService
from ..services.task_service import TaskService
from ..services.approve_quotation_service import ApproveQuotationService
from ..services.assign_booking_service import AssignBookingService
from odoo import exceptions

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
            # Skip if context flag is set to prevent duplicate price request tasks
            if not self.env.context.get('skip_price_request_listener'):
                self._handle_quotation_activated(record)
        elif record.is_cancelled():
            self._handle_quotation_cancelled(record)
        elif record.is_customer_confirmed():
            self._handle_quotation_customer_confirmed(record)
        elif record.is_sale_leader_confirmed():
            self._handle_quotation_sale_leader_confirmed(record)
        elif record.is_order():
            self._handle_quotation_confirmed(record)

    def _handle_quotation_activated(self,record: SaleOrder) -> None:
        project = False
        service = RequestPriceService(self.env)
        project_service = ProjectService(self.env)
        sale_order_lines_without_price = record.get_sale_order_lines_missing_price()
        _logger.info(f"sale_order_lines_without_price: {sale_order_lines_without_price}")

        if not sale_order_lines_without_price:
            return
        
        project = project_service.get_project_by_type(ProjectService.PROJECT_TYPE_PRICE_REQUEST)
        _logger.info(f"project: {project}")
        if not project:
            return
        
        # Filter out lines that were created very recently (within the last few seconds)
        # to avoid duplicate price request tasks for newly created lines
        current_time = fields.Datetime.now()
        recent_lines = sale_order_lines_without_price.filtered(
            lambda line: line.create_date and 
            (current_time - line.create_date).total_seconds() < 5
        )
        
        # Only process lines that are not recently created
        lines_to_process = sale_order_lines_without_price - recent_lines
        
        for sale_order_line in lines_to_process:
            service.create_request_price_task(sale_order_line, sale_order_line.etd_sale)

    def _handle_quotation_confirmed(self,record: SaleOrder) -> None:
        project = False
        service = TaskService(self.env)
        sale_order_lines_with_booking = record.get_sale_order_lines_with_booking()
        _logger.info(f"sale_order_lines_without_price: {sale_order_lines_with_booking}")
        if not sale_order_lines_with_booking:
            return
        else:
            # case 1: request price if needed
            project = service.get_project_by_type(TaskService.PROJECT_TYPE_ASSIGN_BOOKING)
        _logger.info(f"project: {project}")
        if not project:
            return
        for sale_order_line in sale_order_lines_with_booking:
            service.create_task_by_sale_order_line(project.id, TaskService.TASK_TYPE_ASSIGN_BOOKING, sale_order_line)

    def _handle_quotation_cancelled(self,record: SaleOrder) -> None:
        if record.is_cancelled():
            TaskService(self.env).cancel_tasks_by_sale_order(record)

    def  _handle_quotation_customer_confirmed(self, record: SaleOrder) -> None:
        _logger.info(f"_handle_quotation_customer_confirmed {record}")
        service = ApproveQuotationService(self.env)
        service.create_approve_quotation_task(record)

    def _handle_quotation_sale_leader_confirmed(self,record: SaleOrder) -> None:
        _logger.info(f"_handle_quotation_sale_leader_confirmed {record}")
        service = AssignBookingService(self.env)
        sale_order_lines_without_booking = record.get_sale_order_lines_missing_booking()
        for sale_order_line in sale_order_lines_without_booking:
            service.create_assign_booking_task(sale_order_line)
