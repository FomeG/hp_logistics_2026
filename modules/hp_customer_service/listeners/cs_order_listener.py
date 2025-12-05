# -*- coding: utf-8 -*-
# File: events/cs_order_listener.py

from odoo.addons.component.core import Component
from odoo.addons.hp_components.models import constants
<<<<<<< Updated upstream
from ...hp_components.services.department_service import DepartmentService
=======
from ..services.cs_order_service import CsOrderService
>>>>>>> Stashed changes


class CsOrderCreateTruckingListener(Component):
    _name = 'cs.order.create_trucking_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['cs.order']

    # def on_record_write(self, record, fields=None):
    #     """Chỉ chạy khi có thay đổi sale_order_id hoặc booking_id"""
    #     if not record.booking_id:
    #         return
    #
    #     trigger_fields = {'sale_order_id', 'booking_id', 'state'}
    #     if fields and not (fields & trigger_fields):
    #         return
    #
    #     # Chỉ tạo khi CS Order đã ở trạng thái In Progress hoặc Done
    #     if record.state not in ['in_progress', 'done']:
    #         return
    #
    #     # Gọi hàm tạo Plan/Job/Trip
    #     record.sudo()._auto_create_trucking_from_cs_order()

    # def on_record_create(self, record, fields=None):
    #     """Khi tạo mới cũng kiểm tra luôn"""
    #     record.sudo()._auto_create_trucking_from_cs_order()
    #
    # def on_record_write(self, record, fields=None):
    #     if 'booking_id' in fields and record.booking_id:
    #         record.sudo()._auto_create_trucking_from_cs_order()

    def on_record_create(self, record, fields=None):
<<<<<<< Updated upstream
        if not record.booking_id:
            return
        record.sudo()._auto_create_trucking_from_cs_order()
        plan = record.env['trucking_planning.plan'].sudo().search([
            ('cs_order_id', '=', record.id)
        ], limit=1)
=======
        if record.booking_id:
            record.sudo()._auto_create_trucking_from_cs_order()
        
        CsOrderService(self.env).assgin_project_task_type_to_cs_order_project(record)
>>>>>>> Stashed changes

        if plan:
            self._send_trucking_notification(record, plan)

    def _send_trucking_notification(self, cs_order, plan):
        trucking_users = DepartmentService(self.env).get_user_by_department_type(DepartmentService.DEPARTMENT_TYPE_TRUCKING)

        if not trucking_users:
            return

        message_title = "New Trucking Plan!"
        message_body = (
            f"Có Plan Trucking mới từ CS!\n\n"
            f"• CS Order: {cs_order.code}\n"
            f"• Booking: {cs_order.booking_id.code or 'N/A'}\n"
            f"• Plan: {plan.name}\n"
            f"• Loại: {'Export' if plan.plan_type == 'export' else 'Import'}\n"
            f"Please review and assign trucks accordingly !"
        )
        for user in trucking_users:
            if user.partner_id:
                self.env['bus.bus'].sudo()._sendone(
                    user.partner_id,
                    'simple_notification',
                    {
                        'title': message_title,
                        'message': message_body,
                        'sticky': True,
                        'warning': False,
                        'type': 'success',
                    }
                )
    # def on_record_write(self, record, fields=None):
    #     if 'booking_id' in fields and record.booking_id:
    #         record.sudo()._auto_create_trucking_from_cs_order()