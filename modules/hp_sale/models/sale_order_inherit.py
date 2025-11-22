from logging import Logger

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
# from odoo.addons.hp_components.services.sale_order_service import SaleOrderService
# from ...hp_components.services.task_service import TaskService
from ...hp_components.models import constants
import logging

_logger: Logger = logging.getLogger(__name__)

class SaleOrderInherrit(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        (constants.SaleOrderState.DRAFT, 'Draft'),
        (constants.SaleOrderState.SENT_TO_CLIENT, 'Sent To Client'),
        (constants.SaleOrderState.REVIEW, 'Review'),
        (constants.SaleOrderState.SENT_TO_LEADER, 'Sent To Leader'),
        (constants.SaleOrderState.SALE, 'Sales Order'),
        (constants.SaleOrderState.DONE, 'Done'),
        (constants.SaleOrderState.CANCELLED, 'Cancelled'),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

    client_id = fields.Many2one(
        comodel_name='res.partner.client',
        # domain="[('user_id', '=', uid)]",
        string='Client',
        required=True,
        tracking=True,
    )
    service_type = fields.Selection(
        constants.ServiceType.SELECT_OPTIONS,
        string="Service Type",
        default=constants.ServiceType.EXPORT,
        required=True,
    )
    incoterm_id = fields.Many2one(
        'account.incoterms',
        string="Incoterm",
        help="International Commercial Term (e.g., FOB, CIF, EXW)."
    )
    branch_id = fields.Many2one(
        comodel_name='hr.branch',
        compute='_compute_branch_id',
        store=True,
        index=True,
    )
    commodity = fields.Char(
        string="Commodity"
    ) # Add commodity field becasuse cs order commodity is related to sale order commodity
    commodity_hs_code = fields.Char(
        string="Commodity HS Code",
    )
    etd = fields.Date(
        string="ETD",
        help="Estimated Time of Departure"
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        store=True,
    )
    @api.onchange("client_id")
    def _onchange_client_id(self):
        if self.client_id and self.client_id.partner_id:
            self.partner_id = self.client_id.partner_id.id if self.client_id else False
        else:
            self.partner_id = False


    # When activate Quotation => check if some product is missing booking/price => make task and assgin to all users relating to the pod
    # def action_activate_quotation(self):
    #     """Submit quotation for customer review."""
    #     self.ensure_one()
    #     if not self.order_line:
    #         raise ValidationError(_("You cannot activate a quotation without any order lines."))

    #     for line in self.order_line:
    #         if line.product_template_id.type == 'pricing':
    #             if not line.container_type_id:
    #                 raise ValidationError(_("Sale order line: '%s' requires a container type.") % line.product_template_id.name)
    #             if not line.etd_sale:
    #                 raise ValidationError(_("Sale order line: '%s' requires a etd sale.") % line.product_template_id.name)

    #     self.write({'state': 'activated'})

    #     return True

    def action_bypass_to_sale(self):
        self.ensure_one()
        self.write({'state': 'sale'})

    def action_convert_to_cs_job(self):
        self.ensure_one()

        # # Kiểm tra xem đã có booking chưa
        # if not self.booking_id:
        #     raise UserError("Vui lòng chọn Booking trước khi convert sang Job.")
        #
        # # Tạo Job mới từ thông tin booking
        # job = self.env['cs.job'].create({
        #     'job_number': "001",
        #     'booking_id': self.booking_id.id,
        #     'service_type': 'door-cy',  # hoặc map từ sale order
        #     'department_code': 'JP01',  # hoặc custom based on user
        #     # 'staff_sales': self.user_id.name if hasattr(self, 'user_id') else '',
        #     'booking_number': self.booking_id.name,
        #     'shipping_line_id': self.booking_id.shipping_line_id.id,
        # })
        #
        # # Mở form view Job vừa tạo
        # return {
        #     'name': 'Customer Service Job',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'cs.job',
        #     'view_mode': 'form',
        #     'res_id': job.id,
        #     'target': 'current',
        # }

    # When customer confirmed => click button to change state and create task for sale leader to confirm
    # def action_customer_confirm(self):
    #     """Submit quotation for customer review after validation."""
    #     return SaleOrderService(self.env).hande_customer_confirm(self)

    # def action_sale_leader_approved(self):
    #     """Move to pricing leader confirmation after sales manager approves."""
    #     self.write({'state': 'sale_leader_confirm'})

    #     return True

    # def action_pricing_leader_approved(self):
    #     """Move to pricing leader confirmation after sales manager approves."""
    #     self.write({'state': 'pricing_leader_confirm'})

    #     return True

    # def action_final_confirm(self):
    #     """Confirm the order after pricing manager approves."""
    #     for order in self:

    #         # First change to a state that the original action_confirm accepts
    #         order.write({'state': 'sent'})

    #         # Now we can call the original confirm method
    #         order.action_confirm()

    #     return True

    # def get_sale_order_lines_missing_price(self):
    #     self.ensure_one()  # Make sure we're working on exactly one sale.order
    #     # Now safe to do single-record operations
    #     return self.order_line.filtered(lambda l: not l.freight_booking_id and not l.freight_quotation_id)
    
    # def get_sale_order_lines_missing_booking(self):
    #     self.ensure_one()
    #     return self.order_line.filtered(lambda l: not l.freight_booking_id)

    # def get_sale_order_lines_with_booking(self):
    #     self.ensure_one()  # Make sure we're working on exactly one sale.order
    #     # Now safe to do single-record operations
    #     return self.order_line.filtered(lambda l: l.freight_booking_id and l.freight_booking_id.booking_status != 'booked')
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

    # def action_create_route(self):
    #     """Open wizard to collect Port/Route information"""
    #     return {
    #         'name': _('Create Port/Route Request'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'freight.purchase.port.route.request.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_sale_order_id': self.id
    #         }
    #     }
    
    def select_pricing_product(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Product Selling Week Line',
            'res_model': 'product.template.selling.week.line',
            'view_mode': 'list,search',
            'views': [
                (self.env.ref('hp_sale.view_product_template_selling_week_line_list').id, 'list'),
                (self.env.ref('hp_sale.view_product_template_selling_week_line_search').id, 'search'),
            ],
            'target': 'new',
            'domain': [],
            'context': {
                'sale_order_id': self.id,
                'default_shipping_line_id': self.shipping_line_id.id,
                'dialog_size': 'extra-large',
                'create': False,
                'select_mode': True,
            },
        }

    def select_normal_product(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Normal Product',
            'res_model': 'product.template',
            'view_mode': 'list,search',
            'views': [
                (self.env.ref('hp_sale.product_template_normal_list_view').id, 'list'),
                (self.env.ref('hp_sale.product_template_normal_search_view').id, 'search'),
            ],
            'target': 'new',
            'domain': [('route_id', '=', False)],
            'context': {
                'sale_order_id': self.id,
                'dialog_size': 'extra-large',
                'create': False,
                'select_mode': True,
                'group_by': 'categ_id',
            },
        }

    # def _handle_quotation_activated(self):
    #     TaskService(self.env)._handle_task_with_quotation_activated(self)

    # def _handle_quotation_cancelled(self):
    #     TaskService(self.env)._handle_task_with_quotation_cancelled(self)

    # def _handle_quotation_customer_confirmed(self):
    #     TaskService(self.env)._handle_task_with_quotation_customer_confirmed(self)

    # def _handle_quotation_sale_leader_confirmed(self):
    #     TaskService(self.env)._handle_task_with_quotation_sale_leader_confirmed(self)

    # def _handle_quotation_confirmed(self):
    #     SaleOrderService(self.env).handle_quotation_confirmed(self)

    @api.depends('client_id')
    def _compute_branch_id(self):
        for record in self:
            partner = self.env.user.partner_id
            branch_id = False
            if partner and partner.branch_id:
                branch_id = partner.branch_id
            if not branch_id:
                branch_id = record.client_id.branch_id

            record.branch_id = branch_id
        
    def action_update_state(self, state):
        self.write({'state': state})

        return True