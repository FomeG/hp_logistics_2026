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
        member = sale_order_line.booking_id.create_uid

        if project and member:
            self.env['project.task'].create({
                'name': f"Approve Booking:{sale_order_line.product_id.product_tmpl_id.name} in {sale_order_line.order_id.name}",
                'project_id': project.id,
                'user_ids': [member.id],
                'sale_order_id': sale_order_line.order_id.id,
                'sale_line_id': sale_order_line.id,
                'booking_id': sale_order_line.booking_id.id,
                'date_assign': datetime.now(),
                'description': f"Approve Booking: for {sale_order_line.product_id.product_tmpl_id.name} in quotation {sale_order_line.order_id.name}",
            })
    
    def handle_approve_booking(self, task):
        self.validate_approve_booking(task)
        # todo

        task.update_done_task()
        return True
    
    def validate_approve_booking(self, task):
        if not task.sale_order_id:
            raise ValidationError(_("Quotation is required."))
        if not task.booking_id:
            raise ValidationError(_("Booking is required."))
        if not task.sale_line_id:
            raise ValidationError(_("Sales order line is required."))