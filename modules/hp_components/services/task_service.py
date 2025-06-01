from .cancel_task_service import CancelTaskService
from .price_request_service import PriceRequestService
from .sale_order_service import SaleOrderService

class TaskService:
    _name = 'task.service'
    TASK_TYPE_PRICE_REQUEST = 'price_request'
    PROJECT_TYPE_PRICE_REQUEST = 'request_price'

    def __init__(self, env):
        self.env = env

    def create_task(self, project_id, task_type, sale_order_line):
        if task_type == self.TASK_TYPE_PRICE_REQUEST:
            PriceRequestService(self.env).create(project_id, sale_order_line)

    def cancel_tasks_by_sale_order(self, sale_order):
            CancelTaskService(self.env).cancel_tasks_by_sale_order(sale_order)

    def update_sale_order_line_price_by_task(self, task):
        """
        apply on price request project
        """
        price_request_project = self.get_project_by_type(TaskService.PROJECT_TYPE_PRICE_REQUEST)
        if task.project_id.id != price_request_project.id:
            return
        service =  SaleOrderService(self.env)
        #todo: check task has been updated with price
        service.update_sale_order_line_price_by_task(project_task=task)

    def get_project_by_type(self, project_type=''):
        project = self.env['project.project'].search([('type', '=', project_type)], limit=1)
        return project if project else False