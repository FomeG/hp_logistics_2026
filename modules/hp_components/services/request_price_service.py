from .base_task_service import BaseTaskService
import logging
from .department_service import DepartmentService
from .project_service import ProjectService
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import _

_logger = logging.getLogger(__name__)

class RequestPriceService(BaseTaskService):
    _name = 'custom_component.price.request.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)
        self.project_service = ProjectService(env)

    def is_sale_order_line_has_product_pricing(self, sale_order_line) -> bool:
        return sale_order_line.product_id.product_tmpl_id.type == 'pricing'

    def create_request_price_task(self, sale_order_line, etd):
        project = self.project_service.get_project_by_type(ProjectService.PROJECT_TYPE_PRICE_REQUEST)
        leader = self.department_service.get_pricing_department_leader()
        leader = leader if leader else self.env.user
        if project and leader:
            task = self.env['project.task'].sudo().with_context(skip_so_confirmation=True).create({
                'name': f'Request price for product: {sale_order_line.product_id.product_tmpl_id.name}',
                'project_id': project.id,
                'sale_order_id': sale_order_line.order_id.id,
                'container_type_id': sale_order_line.container_type_id.id,
                'sale_line_id': sale_order_line.id,
                'user_ids': [leader.id],
                'etd': etd,
                'date_assign': datetime.now(),
            })
            if not task.sale_order_id:
                _logger.info('Attempting to force set sale_order_id via write')
                task.write({'sale_order_id': sale_order_line.order_id.id})
            return True
        return False

    def calculateBasePriceByContainerType(self, quotation, container_type):
        matching_lines = quotation.line_ids.filtered(
            lambda l: l.container_type_id.id == container_type.id
        )

        if not matching_lines:
            raise ValidationError(
                _("No quotation lines found for container type '%s'.") % container_type.name
            )

        return round(sum(matching_lines.mapped('cost')) / len(matching_lines), 2)

    def handle_approve_price(self, task):
        self.validate_approve_price(task)

        # Determine base price based on container type
        base_price = self.calculateBasePriceByContainerType(task.quotation_id, task.sale_line_id.container_type_id)
        if task.sale_line_id:
            task.sale_line_id.sudo().write({
                'freight_quotation_id': task.quotation_id.id,
                'base_price': base_price,
                'price_unit': base_price,
            })

        task.update_done_task()
        return True
    
    def validate_approve_price(self, task):
        if not task.quotation_id:
            raise ValidationError(_("Pricing quotation is required."))

        quotation_line = task.quotation_id.line_ids.filtered(
            lambda line: line.container_type_id.id == task.container_type_id.id
        )
        if not quotation_line:
            raise ValidationError(_(
                "No quotation line found for container type '%s' in this task."
            ) % (task.container_type_id.name or "N/A"))