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

    def _get_sealine_members(self, sale_order_line):
        # Get list of pricing member related to sealine
        region_id = sale_order_line.product_template_id.sealine_id.pod_id.sudo().region_id

        # Find all users in that region
        pricing_member_group = self.env.ref('hp_pricing.group_hp_pricing_member')
        pricing_users_in_region = self.env['res.users'].search([
            ('region_id', '=', region_id.id),
            ('groups_id', 'in', [pricing_member_group.id]),
            ('active', '=', True)
        ])

        if len(pricing_users_in_region) == 1:
            return pricing_users_in_region[0]


    def _create_pricing_task(self,project_id, sale_order_line):
        member = self._get_sealine_members(sale_order_line)
        leader = self.department_service.get_pricing_department_leader()
        if member:
            assignee = member
        elif not member and leader:
            assignee = leader
        else:
            return
        self.env['project.task'].create({
            'name': f"Request price for {sale_order_line.product_id.product_tmpl_id.name}",
            'project_id': project_id,
            'user_ids': [assignee.id],
            'sale_order_id': sale_order_line.order_id.id,
            'sale_line_id': sale_order_line.id,
            'description': f"Need price for {sale_order_line.product_id.product_tmpl_id.name} in quotation {sale_order_line.order_id.name}",
        })