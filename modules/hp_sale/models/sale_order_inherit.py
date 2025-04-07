from odoo import models, fields

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
        ('customer_confirm', "Customer Review"),
        ('sale_leader_confirm', "Sales Leader Review"),
        ('pricing_leader_confirm', "Pricing Leader Review"),
        ('sent', "Quotation Sent"),
        ('sale', "Confirmed"),
        ('cancel', "Cancelled"),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

    def action_customer_confirm(self):
        """Submit quotation for customer review."""
        return self.write({'state': 'customer_confirm'})

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

