from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
import logging
from odoo.addons.hp_pricing.models.inherit_res_users import get_excluded_user_ids

_logger = logging.getLogger(__name__)

class SaleOrderInherrit(models.Model):
    _inherit = 'sale.order'

    booking_ids = fields.Many2many(
        'pricing.booking',
        'sale_order_booking_rel',
        'sale_order_id',
        'booking_id',
        string="Bookings"
    )

    # Override the entire state field
    state = fields.Selection([
        ('draft', "Draft Quotation"),
        ('activated', "Quotation Activated"),
        ('customer_confirm', "Res-Customer Confirmed"),
        ('sale_leader_confirm', "Res-Sales Leader Confirmed"),
        ('pricing_leader_confirm', "Res-Pricing Leader Confirmed"),
        ('sent', "Res-Quotation Sent"),
        ('sale', "Order-Confirmed"),
        ('cancel', "Cancelled"),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

    # When activate Quotation => check if some product is missing booking/price => make task and assgin to all users relating to the pod
    def action_activate_quotation(self):
        """Submit quotation for customer review."""
        self.write({'state': 'activated'})
        self._create_request_price_tasks()
        return True

    def _create_request_price_tasks(self):
        """Create tasks for request_price when quotation is activated."""
        project_request_price = self.env['project.project'].search([('type', '=', 'request_price')], limit=1)

        if not project_request_price:
            return

        for order in self:
            # Find lines with product_type_filter = 'pricing' and missing booking_id
            pricing_lines_without_booking = order.order_line.filtered(
                lambda line: line.product_type_filter == 'pricing' and not line.booking_id
            )

            # Skip if there are no pricing lines without booking
            if not pricing_lines_without_booking:
                continue

            for line in pricing_lines_without_booking:
                # Check if a task already exists for this product/order combination
                existing_task = self.env['project.task'].search([
                    ('sale_order_id', '=', order.id),
                    ('sale_line_id', '=', line.id),
                    ('project_id', '=', project_request_price.id)
                ], limit=1)

                if not existing_task:
                    # Get list of users to exclude
                    excluded_ids = get_excluded_user_ids(self.env)

                    pricing_director_group = self.env.ref('hp_pricing.group_hp_pricing_director')
                    pricing_director = self.env['res.users'].search([
                        ('groups_id', 'in', pricing_director_group.id),
                        ('id', 'not in', excluded_ids),
                        ('active', '=', True)
                    ], limit=1)

                    assignee_ids = []

                    if pricing_director:
                        assignee_ids.append(pricing_director.id)

                    # Create a new task for request_price with assignees
                    task_vals = {
                        'name': f"Request Price for {line.product_id.name}",
                        'project_id': project_request_price.id,
                        'sale_order_id': order.id,
                        'sale_line_id': line.id,
                        'product_template_id': line.product_template_id.id,
                        'etd': line.etd_sale,
                        'date_assign': fields.Datetime.now(),
                    }

                    # Add assignees if found
                    if assignee_ids:
                        task_vals['user_ids'] = [(6, 0, assignee_ids)]

                    self.env['project.task'].sudo().create(task_vals).send_notification_by_stage('open', assignee_ids)

    # When customer confirmed => click button to change state and create task for sale leader to confirm
    def action_customer_confirm(self):
        """Submit quotation for customer review after validation."""
        # Validate all pricing lines have bookings
        pricing_lines_without_booking = self.order_line.filtered(
            lambda line: line.product_type_filter == 'pricing' and not line.booking_id
        )

        if pricing_lines_without_booking:
            product_names = ", ".join(line.product_id.name for line in pricing_lines_without_booking)
            raise ValidationError(_(
                "Cannot proceed to customer confirmation. The following products need a booking assignment: %s"
            ) % product_names)

        # Set state to customer_confirm
        self.write({'state': 'customer_confirm'})

        # Create approval task for team leader
        self._create_approval_tasks_sale_leader()

        return True


    # Ceate task for sale leader to confirm
    def _create_approval_tasks_sale_leader(self):
        """Create tasks for quotation approval by team leader."""
        project_approve_quotation = self.env['project.project'].search([('type', '=', 'approve_quotation')], limit=1)

        if not project_approve_quotation:
            return

        for order in self:
            # Check if a task already exists for this order
            existing_task = self.env['project.task'].search([
                ('sale_order_id', '=', order.id),
                ('project_id', '=', project_approve_quotation.id),
                ('approval_type', '=', 'sale_leader')
            ], limit=1)

            if not existing_task:
                # Get list of users to exclude
                excluded_ids = get_excluded_user_ids(self.env)
                _logger.info(F"excluded_ids: {excluded_ids}")

                # Find sales leader excluding admins/CEOs
                sale_director_group = self.env.ref('sales_team.group_sale_manager')
                sale_director = self.env['res.users'].search([
                    ('groups_id', 'in', sale_director_group.id),
                    ('id', 'not in', excluded_ids),
                    ('active', '=', True)
                ], limit=1)

                assignee_ids = []
                if sale_director:
                    assignee_ids.append(sale_director.id)

                # Create a new task for approval
                task_vals = {
                    'name': f"Sale Leader Approve Quotation: {order.name}",
                    'project_id': project_approve_quotation.id,
                    'sale_order_id': order.id,
                    'date_assign': fields.Datetime.now(),
                    'approval_type': 'sale_leader',
                }

                # Add assignees if found
                if assignee_ids:
                    task_vals['user_ids'] = [(6, 0, assignee_ids)]

                self.env['project.task'].sudo().create(task_vals).send_notification_by_stage('open', assignee_ids)

    def action_sale_leader_approved(self):
        """Move to pricing leader confirmation after sales manager approves."""
        self.write({'state': 'sale_leader_confirm'})

        # Create approval task for pricing team leader
        self._create_approval_tasks_pricing_leader()

        return True

    def action_pricing_leader_approved(self):
        """Move to pricing leader confirmation after sales manager approves."""
        self.write({'state': 'pricing_leader_confirm'})

        return True

    # Ceate task for pricing leader to confirm
    def _create_approval_tasks_pricing_leader(self):
        """Create tasks for quotation approval by pricing leaders."""
        project_approve_quotation = self.env['project.project'].search([('type', '=', 'approve_quotation')], limit=1)

        if not project_approve_quotation:
            return

        for order in self:
            # Check if a task already exists for this order
            existing_task = self.env['project.task'].search([
                ('sale_order_id', '=', order.id),
                ('project_id', '=', project_approve_quotation.id),
                ('approval_type', '=', 'pricing_leader')
            ], limit=1)

            if not existing_task:
                # Get list of users to exclude
                excluded_ids = get_excluded_user_ids(self.env)

                pricing_director_group = self.env.ref('hp_pricing.group_hp_pricing_director')
                pricing_director = self.env['res.users'].search([
                    ('groups_id', 'in', pricing_director_group.id),
                    ('id', 'not in', excluded_ids),
                    ('active', '=', True)
                ], limit=1)

                assignee_ids = []

                if pricing_director:
                    assignee_ids.append(pricing_director.id)

                # Create a new task for approval
                task_vals = {
                    'name': f"Pricing Leader Approval: {order.name}",
                    'project_id': project_approve_quotation.id,
                    'sale_order_id': order.id,
                    'date_assign': fields.Datetime.now(),
                    'approval_type': 'pricing_leader',
                }

                # Add assignees if found
                if assignee_ids:
                    task_vals['user_ids'] = [(6, 0, assignee_ids)]

                self.env['project.task'].sudo().create(task_vals).send_notification_by_stage('open', assignee_ids)

    def action_final_confirm(self):
        """Confirm the order after pricing manager approves."""
        for order in self:
            # Create booking approval tasks for each pricing line with booking
            order._create_booking_approval_tasks()

            # First change to a state that the original action_confirm accepts
            order.write({'state': 'sent'})

            # Now we can call the original confirm method
            order.action_confirm()

        return True

    def _create_booking_approval_tasks(self):
        """Create tasks for approving bookings when a sales order is confirmed."""
        project_approve_booking = self.env['project.project'].search([('type', '=', 'assign_booking')], limit=1)

        if not project_approve_booking:
            return

        for order in self:
            # Find lines with product_type_filter = 'pricing' and having booking_id
            pricing_lines_with_booking = order.order_line.filtered(
                lambda line: line.product_type_filter == 'pricing' and line.booking_id
            )

            for line in pricing_lines_with_booking:
                # Check if a task already exists for this sale line's booking
                existing_task = self.env['project.task'].search([
                    ('sale_order_id', '=', order.id),
                    ('sale_line_id', '=', line.id),
                    ('booking_id', '=', line.booking_id.id),
                    ('project_id', '=', project_approve_booking.id)
                ], limit=1)

                if not existing_task:
                    # Find the booking creator or responsible person to assign
                    assignee_ids = []
                    booking = line.booking_id

                    # First try the creator of the booking
                    if booking.create_uid:
                        assignee_ids.append(booking.create_uid.id)

                    # Create a new task for booking approval
                    task_vals = {
                        'name': f"Approve Booking: {line.product_id.name} in {order.name}",
                        'project_id': project_approve_booking.id,
                        'sale_order_id': order.id,
                        'sale_line_id': line.id,
                        'booking_id': line.booking_id.id,
                        'date_assign': fields.Datetime.now(),
                    }

                    # Add assignees if found
                    if assignee_ids:
                        task_vals['user_ids'] = [(6, 0, assignee_ids)]

                    # Create the task
                    self.env['project.task'].with_context(default_allow_billable=False).sudo().create(task_vals).send_notification_by_stage('open', assignee_ids)

