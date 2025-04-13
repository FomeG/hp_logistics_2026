from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
import logging

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
        ('customer_confirm', "Customer Confirmed"),
        ('sale_leader_confirm', "Sales Leader Confirmed"),
        ('pricing_leader_confirm', "Pricing Leader Confirmed"),
        ('sent', "Quotation Sent"),
        ('sale', "Confirmed"),
        ('cancel', "Cancelled"),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

    # When activate Quotation => check if some product is missing booking/price => make task and assgin to all users relating to the pod
    def action_create_quotation(self):
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
                    ('product_template_id', '=', line.product_id.product_tmpl_id.id),
                    ('project_id', '=', project_request_price.id)
                ], limit=1)

                if not existing_task:
                    # Find pricing members to assign based on the sealine's POD region
                    product_tmpl = line.product_id.product_tmpl_id
                    assignee_ids = []

                    if product_tmpl.sealine_id and product_tmpl.sealine_id.pod_id and product_tmpl.sealine_id.pod_id.region_id:
                        region = product_tmpl.sealine_id.pod_id.region_id
                        # Get users from this region
                        if region.member_ids:
                            assignee_ids = region.member_ids.ids

                    # Create a new task for request_price with assignees
                    task_vals = {
                        'name': f"Request Price for {line.product_id.name}",
                        'project_id': project_request_price.id,
                        'sale_order_id': order.id,
                        'sale_line_id': line.id,
                        'etd': line.etd_sale,
                        'date_assign': fields.Datetime.now(),
                    }

                    # Add assignees if found
                    if assignee_ids:
                        task_vals['user_ids'] = [(6, 0, assignee_ids)]

                    self.env['project.task'].sudo().create(task_vals)

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
                ('project_id', '=', project_approve_quotation.id)
            ], limit=1)

            if not existing_task:
                # Find sales team leader to assign
                assignee_ids = []

                # First try to get from sales team
                if order.team_id and order.team_id.user_id:
                    assignee_ids.append(order.team_id.user_id.id)
                # If no team leader found, try to find from pricing team
                else:
                    # Try to get the sales user creating this order
                    user = self.env.user

                    # First check if this user belongs to a sales team
                    sales_teams = self.env['crm.team'].search([('member_ids', 'in', user.id)])
                    if sales_teams:
                        # Use the team leader of the user's sales team
                        for team in sales_teams:
                            if team.user_id:  # team.user_id is the team leader
                                assignee_ids.append(team.user_id.id)
                                break

                # Create a new task for approval
                task_vals = {
                    'name': f"Approve Quotation: {order.name}",
                    'project_id': project_approve_quotation.id,
                    'sale_order_id': order.id,
                    'date_assign': fields.Datetime.now(),
                }

                # Add assignees if found
                if assignee_ids:
                    task_vals['user_ids'] = [(6, 0, assignee_ids)]

                self.env['project.task'].sudo().create(task_vals)

    def action_customer_approved(self):
        """Move to sales leader confirmation after customer approves."""
        return self.write({'state': 'sale_leader_confirm'})

    def action_sale_leader_approved(self):
        """Move to pricing leader confirmation after sales manager approves."""
        return self.write({'state': 'pricing_leader_confirm'})

    def action_pricing_leader_approved(self):
        """Confirm the order after pricing manager approves."""
        # First change to a state that the original action_confirm accepts
        self.write({'state': 'sent'})
        # Now we can call the original confirm method
        return self.action_confirm()

