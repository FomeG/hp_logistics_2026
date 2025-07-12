from .base_task_service import BaseTaskService
from datetime import datetime
import logging
from .department_service import DepartmentService
from .project_service import ProjectService
from odoo.exceptions import ValidationError
from odoo import _

_logger = logging.getLogger(__name__)


class ApproveQuotationService(BaseTaskService):
    _name = 'custom_component.approve.quotation.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)
        self.project_service = ProjectService(env)

    def is_sale_order_has_product_pricing(self, sale_order) -> bool:
        return any(
            line.product_id.product_tmpl_id.type == 'pricing'
            for line in sale_order.order_line
        )
    
    def create_approve_quotation_task(self, sale_order, department_type):
        project = self.project_service.get_project_by_type(ProjectService.PROJECT_TYPE_APPROVE_QUOTATION)
        if department_type == DepartmentService.DEPARTMENT_TYPE_PRICING:
            leader = self.department_service.get_pricing_department_leader()
        elif department_type == DepartmentService.DEPARTMENT_TYPE_SALE:
            leader = self.department_service.get_sale_department_leader()
        else:
            leader = None

        if project and leader:
            self.env['project.task'].create({
                'name': f"Approve Quotation for: {sale_order.name}",
                'project_id': project.id,
                'user_ids': [leader.id],
                'sale_order_id': sale_order.id,
                'date_assign': datetime.now(),
                'approval_type': department_type,
                'description': f"Need approval for quotation {sale_order.name}",
            })

    def handle_reject_quotation_by_type(self, task, type):
        match type:
            case ProjectService.SALE_TYPE:
                self.validate_by_action(task, ProjectService.ACTION_REJECT_QUOTATION_BY_SALE)
                task.sale_order_id.sudo().write({'state': 'activated'})
            case ProjectService.PRICING_TYPE:
                self.validate_by_action(task, ProjectService.ACTION_REJECT_QUOTATION_BY_PRICING)
                task.sale_order_id.sudo().write({'state': 'customer_confirm'})
            case _:
                return False

        task.update_done_task()
        return True

    def handle_approve_quotation_by_type(self, task, type):
        match type:
            case ProjectService.SALE_TYPE:
                self.validate_by_action(task, ProjectService.ACTION_APPROVE_QUOTATION_BY_SALE)
                task.sale_order_id.sudo().action_sale_leader_approved()
        
            case ProjectService.PRICING_TYPE:
                self.validate_by_action(task, ProjectService.ACTION_APPROVE_QUOTATION_BY_PRICING)
                task.sale_order_id.sudo().action_pricing_leader_approved()
            case _:
                return False

        task.update_done_task()
        return True
    
    def validate_by_action(self, task, action):
        match action:            
            case ProjectService.ACTION_REJECT_QUOTATION_BY_PRICING:
                if not task.sale_order_id or task.sale_order_id.state != 'sale_leader_confirm':
                    raise ValidationError(_("This quotation cannot be rejected in its current state."))
                if not task.rejection_reason:
                    raise ValidationError(_("Please provide a reason for rejection."))
            
            case ProjectService.ACTION_REJECT_QUOTATION_BY_SALE:
                if not task.sale_order_id or task.sale_order_id.state != 'customer_confirm':
                    raise ValidationError(_("This quotation cannot be rejected in its current state."))

                if not task.rejection_reason:
                    raise ValidationError(_("Please provide a reason for rejection."))
            
            case ProjectService.ACTION_APPROVE_QUOTATION_BY_PRICING:
                if not task.sale_order_id or task.sale_order_id.state != 'sale_leader_confirm':
                    raise ValidationError(_("This quotation cannot be approved in its current state."))
            
            case ProjectService.ACTION_APPROVE_QUOTATION_BY_SALE:
                if not task.sale_order_id or task.sale_order_id.state != 'customer_confirm':
                    raise ValidationError(_("This quotation cannot be approved in its current state."))

            case _:
                return