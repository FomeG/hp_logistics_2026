from .cancel_task_service import CancelTaskService
from .request_price_service import RequestPriceService
from .assign_booking_service import AssignBookingService
from .approve_quotation_service import ApproveQuotationService
from .request_product_service import RequestProductService
from .sale_order_service import SaleOrderService
from .department_service import DepartmentService
from .project_service import ProjectService
from odoo import _
from .department_service import DepartmentService
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

    def cancel_tasks_by_sale_order(self, sale_order):
        CancelTaskService(self.env).cancel_tasks_by_sale_order(sale_order)

    def update_sale_order_line_price_by_task(self, task):
        """
        apply on price request project
        """
        price_request_project = self.project_service.get_project_by_type(ProjectService.PROJECT_TYPE_PRICE_REQUEST)
        if task.project_id.id != price_request_project.id:
            return
        service =  SaleOrderService(self.env)
        #todo: check task has been updated with price
        service.update_sale_order_line_price_by_task(project_task=task)
    

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
    