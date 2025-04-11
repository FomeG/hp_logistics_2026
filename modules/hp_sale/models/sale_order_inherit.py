from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError

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
        ('activated', "Ongoing Quotation"),
        ('customer_confirm', "Customer Review"),
        ('sale_leader_confirm', "Sales Leader Review"),
        ('pricing_leader_confirm', "Pricing Leader Review"),
        ('sent', "Quotation Sent"),
        ('sale', "Confirmed"),
        ('cancel', "Cancelled"),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

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
                    # Create a new task for request_price
                    self.env['project.task'].sudo().create({
                        'name': f"Request Price for {line.product_id.name}",
                        'project_id': project_request_price.id,
                        'sale_order_id': order.id,
                        'product_template_id': line.product_id.product_tmpl_id.id,
                        'etd': line.etd_sale,
                        'date_assign': fields.Datetime.now(),
                    })

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
        self._create_approval_tasks()

        return True

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

