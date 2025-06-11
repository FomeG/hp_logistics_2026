from .base_task_service import BaseTaskService
from odoo.addons.hp_sale.models.sale_order_inherit import SaleOrderInherrit
from odoo import fields
import logging
from .department_service import DepartmentService

_logger = logging.getLogger(__name__)


class BookingApprovalService(BaseTaskService):
    _name = 'custom_component.booking.approval.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)

    def create(self,project_id, sale_order_line):
        task = self._sale_order_line_has_open_task(sale_order_line)
        if task:
            return
        if self._is_pricing_type_sale_order_line_with_booking(sale_order_line):
            self._create_confirm_booking_task(project_id, sale_order_line)

    def _is_pricing_type_sale_order_line_with_booking_not_booked(self,sale_order_line) -> bool:
        return sale_order_line.product_id.product_tmpl_id.type == 'pricing' and sale_order_line.booking_id and sale_order_line.booking_id.booking_status != 'booked'

    def _is_pricing_type_sale_order_line_with_booking_not_booked(self,project_id, sale_order_line):
        member = sale_order_line.booking_id.create_uid
        if member:
            assignee = member
        else:
            return
        self.env['project.task'].create({
            'name': f"Approve Booking:{sale_order_line.product_id.product_tmpl_id.name} in {sale_order_line.order_id.name}",
            'project_id': project_id,
            'user_ids': [assignee.id],
            'sale_order_id': sale_order_line.order_id.id,
            'sale_line_id': sale_order_line.id,
            'booking_id': sale_order_line.booking_id.id,
            'date_assign': fields.Datetime.now(),
            'description': f"Approve Booking: for {sale_order_line.product_id.product_tmpl_id.name} in quotation {sale_order_line.order_id.name}",
        })