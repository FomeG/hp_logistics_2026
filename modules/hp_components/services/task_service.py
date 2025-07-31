from .cancel_task_service import CancelTaskService
from .request_price_service import RequestPriceService
from .assign_booking_service import AssignBookingService
from .approve_quotation_service import ApproveQuotationService
from .request_product_service import RequestProductService
from .department_service import DepartmentService
from .project_service import ProjectService
from ..services.activity_service import ActivityService
from odoo import _
from .department_service import DepartmentService
from odoo.addons.sale.models.sale_order import SaleOrder
from odoo import fields
import logging

_logger = logging.getLogger(__name__)

class TaskService:
    _name = 'task.service'

    def __init__(self, env):
        self.env = env
        self.department_service = DepartmentService(env)
        self.project_service = ProjectService(env)
        self.request_product_service = RequestProductService(env)
        self.request_price_service = RequestPriceService(env)
        self.assign_booking_service = AssignBookingService(env)
        self.approve_quotation_service = ApproveQuotationService(env)
        self.cancel_task_service =  CancelTaskService(env)


    def handle_by_action(self, record, action):
        match action:            
            case ProjectService.ACTION_APPROVE_POL_POL:
                self.request_product_service.handle_approve_product(record)
            
            case ProjectService.ACTION_APPROVE_PRICE:
                self.request_price_service.handle_approve_price(record)
            
            case ProjectService.ACTION_APPROVE_QUOTATION_BY_SALE:
                self.approve_quotation_service.handle_approve_quotation_by_sale(record)

            case ProjectService.ACTION_REJECT_QUOTATION_BY_SALE:
                self.approve_quotation_service.handle_reject_quotation_by_sale(record)
            
            case ProjectService.ACTION_ASSIGN_BOOKING:
                self.assign_booking_service.handle_assign_booking(record)

            case _:
                return False
        
        return True

    def _handle_task_with_quotation_activated(self,record: SaleOrder) -> None:
        _logger.info(f"_handle_task_with_quotation_activated {record}")
        sale_order_lines_without_price = record.get_sale_order_lines_missing_price()
        if not sale_order_lines_without_price:
            return
        
        project = self.project_service.get_project_by_type(ProjectService.PROJECT_TYPE_PRICE_REQUEST)
        _logger.info(f"project: {project}")
        if not project:
            return
        
        # Filter out lines that were created very recently (within the last few seconds)
        # to avoid duplicate price request tasks for newly created lines
        current_time = fields.Datetime.now()
        recent_lines = sale_order_lines_without_price.filtered(
            lambda line: line.create_date and (current_time - line.create_date).total_seconds() < 5
        )
        
        # Only process lines that are not recently created
        lines_to_process = sale_order_lines_without_price - recent_lines
        for sale_order_line in lines_to_process:
            self.request_price_service.create_request_price_task(sale_order_line, sale_order_line.etd_sale)
    
    def _handle_task_with_quotation_cancelled(self, record: SaleOrder) -> None:
        _logger.info(f"_handle_task_with_quotation_cancelled {record}")
        if record.is_cancelled():
            self.cancel_task_service.cancel_tasks_by_sale_order(record)

    def  _handle_task_with_quotation_customer_confirmed(self, record: SaleOrder) -> None:
        _logger.info(f"_handle_task_with_quotation_customer_confirmed {record}")
        self.approve_quotation_service.create_approve_quotation_task(record)

    def _handle_task_with_quotation_sale_leader_confirmed(self, record: SaleOrder) -> None:
        _logger.info(f"_handle_task_with_quotation_sale_leader_confirmed {record}")
        sale_order_lines_without_booking = record.get_sale_order_lines_missing_booking()
        for sale_order_line in sale_order_lines_without_booking:
            self.assign_booking_service.create_assign_booking_task(sale_order_line)

    def notify_task_done(self, task):
        creator = task.create_uid
        if creator:
            service = ActivityService(
                env=self.env,
                model_name='project.task',
                record_id=task.id,
                user_ids=creator.id)
            service._create_activity_by_type(
                'mail.mail_activity_data_todo',
                summary='Task has been completed',
                note=f'<p>Your task has been completed.: <b>{task.name}</b></p>'
            )
    
    def notify_task_open(self, task):
        if task.user_ids:
            service = ActivityService(
                env=self.env,
                model_name='project.task',
                record_id=task.id,
                user_ids=task.user_ids.ids)
            service.create_price_request(
                summary='New Task Assigned',
                note=f'<p>You have been assigned a new task: <b>{task.name}</b></p>'
            )