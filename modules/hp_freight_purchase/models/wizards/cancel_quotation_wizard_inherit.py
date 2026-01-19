from odoo import models, _
from odoo.addons.hp_components.services.activity_service import ActivityService
from odoo.addons.hp_components.services.department_service import DepartmentService


class CancelQuotationWizardInherit(models.TransientModel):
    _inherit = 'hp_sale.cancel.quotation.wizard'

    def _handle_cancel_notifications(self, order, old_state):
        super()._handle_cancel_notifications(order, old_state)

        if order.booking_line_id:
            self._release_booking_and_notify(order, self.env.user.name)

    def _release_booking_and_notify(self, order, user_name):
        """Release booking and notify pricing team and sale leader."""
        booking_line = order.booking_line_id
        if not booking_line:
            return

        # Release booking (unlink from sale order)
        order.write({'booking_line_id': False})

        # Notify booking creator (pricing member)
        if booking_line.create_uid:
            service = ActivityService(
                env=self.env,
                model_name='freight.purchase.booking.line',
                record_id=booking_line.id,
                user_ids=booking_line.create_uid.id
            )

            summary = _("Booking has been released from quotation %s (cancelled by %s)") % (
                order.name,
                user_name
            )

            service._create_activity_by_type(
                summary=summary,
                note=self.cancel_reason
            )

        # Also notify sale leader
        dept_service = DepartmentService(self.env)
        sale_leader = dept_service.get_department_manager_by_employee(
            self.env.user.employee_id
        )

        if sale_leader:
            service = ActivityService(
                env=self.env,
                model_name='sale.order',
                record_id=order.id,
                user_ids=sale_leader.id
            )

            summary = _("Booking released from quotation %s (cancelled by %s)") % (
                order.name,
                user_name
            )

            service._create_activity_by_type(
                summary=summary,
                note=self.cancel_reason
            )
