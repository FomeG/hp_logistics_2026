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
        """Release booking and notify booking provider and sale leader."""
        booking_line = order.booking_line_id
        booking_provider = order.booking_provider_id
        if not booking_line:
            return

        booking_code = order.booking_code or (booking_line.booking_id.name if booking_line.booking_id else 'N/A')

        # Notify booking provider (pricing member who assigned the booking)
        if booking_provider:
            service = ActivityService(
                env=self.env,
                model_name='sale.order',
                record_id=order.id,
                user_ids=booking_provider.id
            )

            summary = _("Quotation %s has been cancelled by %s. Booking %s has been released.") % (
                order.name,
                user_name,
                booking_code
            )

            service._create_activity_by_type(
                summary=summary,
                note=_("Reason: %s") % self.cancel_reason
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

            summary = _("Booking %s released from quotation %s (cancelled by %s)") % (
                booking_code,
                order.name,
                user_name
            )

            service._create_activity_by_type(
                summary=summary,
                note=_("Reason: %s") % self.cancel_reason
            )


        # Release booking logic
        if booking_line:
            # Update status sang cancelled để trigger listener hoàn lại quantity
            booking_line.write({'status': 'cancelled'})
    


        # Release booking from quotation
        order.write({
            'booking_line_id': False,
            'booking_provider_id': False,
        })
