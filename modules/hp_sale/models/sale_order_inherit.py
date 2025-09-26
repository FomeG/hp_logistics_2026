from logging import Logger

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
from odoo.addons.hp_components.services.sale_order_service import SaleOrderService
from ...hp_components.services.task_service import TaskService
import logging

_logger: Logger = logging.getLogger(__name__)

class SaleOrderInherrit(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('activated', 'Quotation Activated'),
        ('customer_confirm', 'Customer Confirmed'),
        ('sale_leader_confirm', 'Sales Leader Confirmed'),
        ('pricing_leader_confirm', 'Pricing Leader Confirmed'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

    client_id = fields.Many2one(
        comodel_name='res.partner.client',
        string='Client',
        required=True,
        tracking=True,
    )

    @api.onchange("client_id")
    def _onchange_client_id(self):
        if self.client_id and self.client_id.partner_id:
            self.partner_id = self.client_id.partner_id.id if self.client_id else False
        else:
            self.partner_id = False


    # When activate Quotation => check if some product is missing booking/price => make task and assgin to all users relating to the pod
    def action_activate_quotation(self):
        """Submit quotation for customer review."""
        self.ensure_one()
        if not self.order_line:
            raise ValidationError(_("You cannot activate a quotation without any order lines."))

        for line in self.order_line:
            if line.product_template_id.type == 'pricing':
                if not line.container_type_id:
                    raise ValidationError(_("Sale order line: '%s' requires a container type.") % line.product_template_id.name)
                if not line.etd_sale:
                    raise ValidationError(_("Sale order line: '%s' requires a etd sale.") % line.product_template_id.name)

        self.write({'state': 'activated'})

        return True

    # When customer confirmed => click button to change state and create task for sale leader to confirm
    def action_customer_confirm(self):
        """Submit quotation for customer review after validation."""
        return SaleOrderService(self.env).hande_customer_confirm(self)

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

    def get_sale_order_lines_missing_price(self):
        self.ensure_one()  # Make sure we're working on exactly one sale.order
        # Now safe to do single-record operations
        return self.order_line.filtered(lambda l: not l.freight_booking_id and not l.freight_quotation_id)
    
    def get_sale_order_lines_missing_booking(self):
        self.ensure_one()
        return self.order_line.filtered(lambda l: not l.freight_booking_id)

    def get_sale_order_lines_with_booking(self):
        self.ensure_one()  # Make sure we're working on exactly one sale.order
        # Now safe to do single-record operations
        return self.order_line.filtered(lambda l: l.freight_booking_id and l.freight_booking_id.booking_status != 'booked')
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

    def action_create_route(self):
        """Open wizard to collect Port/Route information"""
        return {
            'name': _('Create Port/Route Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.port.route.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id
            }
        }
    
    def _handle_quotation_activated(self):
        TaskService(self.env)._handle_task_with_quotation_activated(self)

    def _handle_quotation_cancelled(self):
        TaskService(self.env)._handle_task_with_quotation_cancelled(self)

    def _handle_quotation_customer_confirmed(self):
        TaskService(self.env)._handle_task_with_quotation_customer_confirmed(self)

    def _handle_quotation_sale_leader_confirmed(self):
        TaskService(self.env)._handle_task_with_quotation_sale_leader_confirmed(self)

    def _handle_quotation_confirmed(self):
        SaleOrderService(self.env).handle_quotation_confirmed(self)