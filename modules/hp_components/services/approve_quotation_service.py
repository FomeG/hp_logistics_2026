from .base_task_service import BaseTaskService
from odoo.addons.hp_sale.models.sale_order_inherit import SaleOrderInherrit
from odoo import fields
import logging
from .department_service import DepartmentService

_logger = logging.getLogger(__name__)


class ApproveQuotationService(BaseTaskService):
    _name = 'custom_component.approve.quotation.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)

    def create(self,department_type, project_id, sale_order):
        task = self._get_open_tasks_by_sale_order(sale_order)
        _logger.info(f"task: {task}")
        if len(task) > 0:
            return
        if self._is_pricing_type_sale_order(sale_order):
            self._create_approval_task(department_type, project_id, sale_order)

    def _is_pricing_type_sale_order(self, sale_order) -> bool:
        return any(
            line.product_id.product_tmpl_id.type == 'pricing'
            for line in sale_order.order_line
        )

    def _create_approval_task(self,department_type, project_id, sale_order):
        leader = self.department_service._get_department_leader_by_type(department_type)
        _logger.info(f"leader: {leader}")
        approval_type = 'sale_leader' if department_type == 'sale' else 'pricing_leader'
        if not leader:
            return
        self.env['project.task'].create({
            'name': f"Approve Quotation for: {sale_order.name}",
            'project_id': project_id,
            'user_ids': [leader.id],
            'sale_order_id': sale_order.id,
            'date_assign': fields.Datetime.now(),
            'approval_type': approval_type,
            'description': f"Need approval for quotation {sale_order.name}",
        })