from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_components.models import constants
from odoo.addons.hp_components.services.activity_service import ActivityService
from odoo.addons.hp_components.services.department_service import DepartmentService


class CancelQuotationWizard(models.TransientModel):
    _name = 'hp_sale.cancel.quotation.wizard'
    _description = 'Cancel Quotation Wizard'

    order_id = fields.Many2one(
        'sale.order',
        string='Quotation',
        required=True,
        ondelete='cascade',
    )
    cancel_reason = fields.Text(
        string='Cancel Reason',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            defaults['order_id'] = self.env.context['active_id']
        return defaults

    def action_confirm_cancel(self):
        self.ensure_one()
        if not self.cancel_reason:
            raise UserError(_('Please provide a reason for cancellation.'))

        order = self.order_id
        old_state = order.state

        # Cancel the quotation
        order.write({
            'state': 'cancel',
            'cancel_reason': self.cancel_reason,
            'cancelled_by_id': self.env.user.id,
        })

        # Handle notifications
        self._handle_cancel_notifications(order, old_state)

        return {'type': 'ir.actions.act_window_close'}

    def _handle_cancel_notifications(self, order, old_state):
        """Handle notifications when quotation is cancelled.
        
        This method can be extended by other modules to add additional
        notification logic (e.g., booking release notifications).
        """
        user_name = self.env.user.name

        # If state was 'request_booking', notify sale leader
        if old_state == constants.SaleOrderState.REQUEST_BOOKING:
            self._notify_sale_leader(order, user_name)

    def _notify_sale_leader(self, order, user_name):
        """Notify sale leader about cancelled quotation."""
        dept_service = DepartmentService(self.env)
        sale_leader = dept_service.get_department_manager_by_employee(
            self.env.user.employee_id
        )

        if not sale_leader:
            return

        service = ActivityService(
            env=self.env,
            model_name='sale.order',
            record_id=order.id,
            user_ids=sale_leader.id
        )

        summary = _("Quotation %s has been cancelled by %s for reason: %s") % (
            order.name,
            user_name,
            self.cancel_reason
        )

        service._create_activity_by_type(
            summary=summary,
            note=self.cancel_reason
        )
