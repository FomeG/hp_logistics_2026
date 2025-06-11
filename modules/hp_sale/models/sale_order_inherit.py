from logging import Logger

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
import logging
from odoo.addons.hp_employee.models.hr_department_inherit import HpDepartmentInherit

_logger: Logger = logging.getLogger(__name__)

class SaleOrderInherrit(models.Model):
    _inherit = 'sale.order'

    booking_ids = fields.Many2many(
        'pricing.booking',
        'sale_order_booking_rel',
        'sale_order_id',
        'booking_id',
        string="Bookings"
    )

    state = fields.Selection(selection_add=[
        ('activated', 'Quotation Activated'),
        ('customer_confirm', 'Customer Confirmed'),
        ('sale_leader_confirm', 'Sales Leader Confirmed'),
        ('pricing_leader_confirm', 'Pricing Leader Confirmed'),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

    # When activate Quotation => check if some product is missing booking/price => make task and assgin to all users relating to the pod
    def action_activate_quotation(self):
        """Submit quotation for customer review."""
        self.write({'state': 'activated'})

        return True

    # When customer confirmed => click button to change state and create task for sale leader to confirm
    def action_customer_confirm(self):
        """Submit quotation for customer review after validation."""
        # Validate all pricing lines have bookings
        pricing_lines_without_price = self.order_line.filtered(
            lambda line: line.product_type_filter == 'pricing' and not line.booking_id and not line.pricing_quotation_id
        )

        if pricing_lines_without_price:
            product_names = ", ".join(line.product_id.name for line in pricing_lines_without_price)
            raise ValidationError(_(
                "Cannot proceed to customer confirmation. The following products need a booking assignment: %s"
            ) % product_names)

        for line in self.order_line:
            if line.price_unit < line.base_price:
                raise ValidationError(_(
                    "The Price unit can not less than Base price"
                ))

        # Set state to customer_confirm
        self.write({'state': 'customer_confirm'})

        return True

    def action_sale_leader_approved(self):
        """Move to pricing leader confirmation after sales manager approves."""
        self.write({'state': 'sale_leader_confirm'})

        return True

    def action_pricing_leader_approved(self):
        """Move to pricing leader confirmation after sales manager approves."""
        self.write({'state': 'pricing_leader_confirm'})

        return True

    def action_final_confirm(self):
        """Confirm the order after pricing manager approves."""
        for order in self:

            # First change to a state that the original action_confirm accepts
            order.write({'state': 'sent'})

            # Now we can call the original confirm method
            order.action_confirm()

        return True

    # def _create_booking_approval_tasks(self):
    #     """Create tasks for approving bookings when a sales order is confirmed."""
    #     project_approve_booking = self.env['project.project'].search([('type', '=', 'assign_booking')], limit=1)
    #
    #     if not project_approve_booking:
    #         return
    #
    #     for order in self:
    #         # Find lines with product_type_filter = 'pricing' and having booking_id
    #         pricing_lines_with_booking = order.order_line.filtered(
    #             lambda line: line.product_type_filter == 'pricing' and line.booking_id
    #         )
    #
    #         for line in pricing_lines_with_booking:
    #             # Check if a task already exists for this sale line's booking
    #             existing_task = self.env['project.task'].search([
    #                 ('sale_order_id', '=', order.id),
    #                 ('sale_line_id', '=', line.id),
    #                 ('booking_id', '=', line.booking_id.id),
    #                 ('project_id', '=', project_approve_booking.id)
    #             ], limit=1)
    #
    #             if not existing_task:
    #                 # Find the booking creator or responsible person to assign
    #                 assignee_ids = []
    #                 booking = line.booking_id
    #
    #                 # First try the creator of the booking
    #                 if booking.create_uid:
    #                     assignee_ids.append(booking.create_uid.id)
    #
    #                 # Create a new task for booking approval
    #                 task_vals = {
    #                     'name': f"Approve Booking: {line.product_id.name} in {order.name}",
    #                     'project_id': project_approve_booking.id,
    #                     'sale_order_id': order.id,
    #                     'sale_line_id': line.id,
    #                     'booking_id': line.booking_id.id,
    #                     'date_assign': fields.Datetime.now(),
    #                 }
    #
    #                 # Add assignees if found
    #                 if assignee_ids:
    #                     task_vals['user_ids'] = [(6, 0, assignee_ids)]
    #
    #                 # Create the task
    #                 self.env['project.task'].with_context(default_allow_billable=False).sudo().create(task_vals)

    def get_sale_order_lines_missing_price(self):
        self.ensure_one()  # Make sure we're working on exactly one sale.order
        # Now safe to do single-record operations
        return self.order_line.filtered(lambda l: not l.booking_id and not l.pricing_quotation_id)

    def get_sale_order_lines_with_booking(self):
        self.ensure_one()  # Make sure we're working on exactly one sale.order
        # Now safe to do single-record operations
        return self.order_line.filtered(lambda l: l.booking_id and l.booking_id.booking_status != 'booked')
    def is_cancelled(self):
        return self.state == 'cancel'
    def is_activated(self):
        return  self.state == 'activated'
    def is_sale_leader_confirmed(self):
        return self.state == 'sale_leader_confirm'
    def is_customer_confirmed(self):
        return self.state == 'customer_confirm'
    def is_order(self):
        return self.state == 'sent'
    def can_update_price(self):
        return self.state in ['draft','activated']