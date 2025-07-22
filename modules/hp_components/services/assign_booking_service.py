from .base_task_service import BaseTaskService
from datetime import datetime
import logging
from .department_service import DepartmentService
from .project_service import ProjectService
from odoo.exceptions import ValidationError
from odoo import _

_logger = logging.getLogger(__name__)

class AssignBookingService(BaseTaskService):
    _name = 'custom_component.booking.approval.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)
        self.project_service = ProjectService(env)

    def is_sale_order_line_not_booking(self, sale_order_line) -> bool:
        return sale_order_line.product_id.product_tmpl_id.type == 'pricing' and sale_order_line.booking_id and sale_order_line.booking_id.booking_status != 'booked'

    def create_assign_booking_task(self, sale_order_line):
        project = self.project_service.get_project_by_type(ProjectService.PROJECT_TYPE_ASSIGN_BOOKING)
        leader = self.department_service.get_pricing_department_leader()

        if project and leader:
            booking = self.find_booking_assign_to_task(sale_order_line.freight_quotation_id, sale_order_line.container_type_id)
            task = self.env['project.task'].create({
                'name': f"Assign Booking for Product: {sale_order_line.product_id.product_tmpl_id.name} in {sale_order_line.order_id.name}",
                'project_id': project.id,
                'user_ids': [leader.id],
                'sale_order_id': sale_order_line.order_id.id,
                'sale_line_id': sale_order_line.id,
                'container_type_id': sale_order_line.container_type_id.id,
                'quotation_id': sale_order_line.freight_quotation_id.id,
                'booking_id': booking.id if booking else False,
                'date_assign': datetime.now(),
            })
            if not task.sale_order_id:
                task.write({'sale_order_id': sale_order_line.order_id.id})
        
    def find_booking_line_by_quotation_and_container_type(self, quotation, container_type):
        quotation_line = quotation.line_ids.filtered(
            lambda line: line.container_type_id.id == container_type.id
        )

        if not quotation_line:
            return False

        booking_line = self.env['freight.purchase.booking.line'].sudo().search([
            ('quotation_line_id', '=', quotation_line[0].id),
            ('status', '!=', 'cancelled'),
        ], limit=1)

        return booking_line if booking_line else False

    def find_booking_assign_to_task(self, quotation, container_type):
        booking_line = self.find_booking_line_by_quotation_and_container_type(quotation, container_type)
        return booking_line.booking_id if booking_line else False
    
    def handle_assign_booking(self, task):
        self.validate_assign_booking(task)
        task.sale_line_id.sudo().write({
            'freight_booking_id': task.booking_id.id,
        })
        task.sale_order_id.sudo().action_pricing_leader_approved()
        task.update_done_task()
        return True
    
    def validate_assign_booking(self, task):
        if not task.sale_line_id:
            raise ValidationError(_("Sale order line is required."))
        if not task.sale_order_id or task.sale_order_id.state != 'sale_leader_confirm':
            raise ValidationError(_("This quotation cannot be approved in its current state."))
        if not task.booking_id:
            raise ValidationError(_("Booking is required."))