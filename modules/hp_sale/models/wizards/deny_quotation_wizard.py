from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_components.models import constants
from odoo.addons.hp_components.services.activity_service import ActivityService


class DenyQuotationWizard(models.TransientModel):
    _name = 'hp_sale.deny.quotation.wizard'
    _description = 'Deny Quotation Wizard'

    order_id = fields.Many2one(
        'sale.order',
        string='Quotation',
        required=True,
        ondelete='cascade',
    )
    deny_reason_type = fields.Selection(
        [
            ('price_is_low', 'Price is low'),
            ('other', 'Other'),
        ],
        string='Reason',
        required=True,
        default='price_is_low',
    )
    deny_reason = fields.Text(
        string='Deny Reason',
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            defaults['order_id'] = self.env.context['active_id']
        return defaults

    def action_confirm_deny(self):
        self.ensure_one()
        
        # Determine the final reason text
        if self.deny_reason_type == 'other':
            if not self.deny_reason:
                raise UserError(_('Please provide a reason for denial.'))
            final_reason = self.deny_reason
        else:
            # Get the label from selection
            final_reason = dict(self._fields['deny_reason_type'].selection).get(self.deny_reason_type)

        order = self.order_id

        # Deny the quotation
        order.write({
            'state': constants.SaleOrderState.DENIED,
            'deny_reason': final_reason,
            'denied_by_id': self.env.user.id,
        })

        # Handle notifications
        self._handle_deny_notifications(order, final_reason)

        return {'type': 'ir.actions.act_window_close'}

    def _handle_deny_notifications(self, order, reason):
        """Handle notifications when quotation is denied.

        Notify the sale member (user_id) responsible for the quotation.
        """
        self._notify_sale_member(order, reason)

    def _notify_sale_member(self, order, reason):
        """Notify sale member about denied quotation."""
        sale_member = order.user_id
        if not sale_member:
            return

        user_name = self.env.user.name

        service = ActivityService(
            env=self.env,
            model_name='sale.order',
            record_id=order.id,
            user_ids=sale_member.id
        )

        summary = _("Quotation %s has been denied by %s for reason: %s") % (
            order.name,
            user_name,
            reason
        )

        service._create_activity_by_type(
            summary=summary,
            note=reason
        )
