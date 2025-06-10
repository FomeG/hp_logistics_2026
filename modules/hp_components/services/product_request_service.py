from .base_task_service import BaseTaskService
from odoo.addons.hp_sale.models.sale_order_inherit import SaleOrderInherrit
import logging
from .department_service import DepartmentService

_logger = logging.getLogger(__name__)


class ProductRequestService(BaseTaskService):
    _name = 'custom_component.product.request.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)

    def _create_product_request_task(self,project_id, sale_order, etd, pod_name_request, pol_name_request, volume_cont):
        leader = self.department_service.get_pricing_department_leader()
        if leader:
            assignee = leader
        else:
            return
        self.env['project.task'].create({
            'name': f'POD/POL Request for {sale_order.name}',
            'project_id': project_id,
            'sale_order_id': sale_order.id,
            'user_ids': [assignee.id],
            'etd': etd,
            'pod_name_request': pod_name_request,
            'pol_name_request': pol_name_request,
            'volume_cont': volume_cont,
            'description': f"Need new product for quotation {sale_order.name}",
        })