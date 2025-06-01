from .base_task_service import BaseTaskService
from odoo.addons.hp_sale.models.sale_order_inherit import SaleOrderInherrit
import logging
from .department_service import DepartmentService

_logger = logging.getLogger(__name__)


class PriceRequestService(BaseTaskService):
    _name = 'custom_component.price.request.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)

    def create(self,project_id, sale_order_line):
        task = self._sale_order_line_has_open_task(sale_order_line)
        if task:
            return
        if self._is_pricing_type_sale_order_line(sale_order_line):
            self._create_pricing_task(project_id, sale_order_line)

    def _is_pricing_type_sale_order_line(self,sale_order_line) -> bool:
        return sale_order_line.product_id.product_tmpl_id.type == 'pricing'

    def _get_sealine_members(self):
        return

    def _create_pricing_task(self,project_id, sale_order_line):
        leader = self.department_service.get_pricing_department_leader()
        if not leader:
            return
        self.env['project.task'].create({
            'name': f"Request price for {sale_order_line.product_id.product_tmpl_id.name}",
            'project_id': project_id,
            'user_ids': [leader.id],
            'sale_order_id': sale_order_line.order_id.id,
            'sale_line_id': sale_order_line.id,
            'description': f"Need price for {sale_order_line.product_id.product_tmpl_id.name} in quotation {sale_order_line.order_id.name}",
        })