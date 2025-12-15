from datetime import timedelta
from logging import Logger
from odoo import models, fields, _, api
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError, AccessError
from ...hp_components.models import constants
import logging

_logger: Logger = logging.getLogger(__name__)

class SaleOrderInherit(models.Model):
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
        string='Client',
        required=True,
        tracking=True,
        domain=lambda self: self._get_client_domain(),
    )
    client_vat = fields.Char(
        string="Tax Code",
        related='client_id.vat',
        store=False
    )
    client_address = fields.Char(
        string="Address",
        related='client_id.address_display',
        store=False
    )
    client_phone = fields.Char(
        string="Phone",
        related='client_id.phone',
        store=False
    )
    client_email = fields.Char(
        string="Email",
        related='client_id.email',
        store=False
    )
    service_type = fields.Selection(
        constants.ServiceType.SELECT_OPTIONS,
        string="Service Type",
        default=constants.ServiceType.EXPORT,
        required=True,
    )
    main_transport_mode = fields.Selection(
        constants.TransportMode.SELECT_OPTIONS,
        string="Main Transport Mode",
        default=constants.TransportMode.SEA,
        required=True,
    )
    goods_location_id = fields.Many2one(
        comodel_name='location.base',
        string="Goods Location",
        domain="[('is_local', '=', True),('type','not in', ['port'])]",
    )
    from_location_id = fields.Many2one(
        comodel_name='location.base',
        string="From Location"
    )
    to_location_id = fields.Many2one(
        comodel_name='location.base',
        string="To Location",
    )
    is_sea_exp_location = fields.Boolean(
        string="Is Export Location",
        compute='_compute_is_sea_exp_location',
        store=False,
    )
    exp_from_location_id = fields.Many2one(
        comodel_name='location.base',
        string="POL",
        domain="[('is_local', '=', True),('type', '=','port')]",
        store=False,
    )
    exp_to_location_id = fields.Many2one(
        comodel_name='location.base',
        string="POD",
        domain="[('is_local', '=', False),('type', '=','port')]",
        store=False,
    )
    imp_from_location_id = fields.Many2one(
        comodel_name='location.base',
        string="From",
        domain="[('is_local', '=', True)]",
        store=False,
    )
    imp_to_location_id = fields.Many2one(
        comodel_name='location.base',
        string="To",
        store=False,
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
        help="Estimated Time of Departure",
        required=True,
        default=lambda self: fields.Date.today() + timedelta(days=1)
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        string="Shipping Line preferred",
    )
    container_type_id = fields.Many2one(
        comodel_name='container.type',
        string="Container Type preferred",
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
        SelllingWeek = self.env['selling.week']
        selling_weeks = SelllingWeek.search([
            ('start_date', '<=', self.etd),
            ('end_date', '>=', self.etd),
        ])

        if not selling_weeks:
            selling_weeks = SelllingWeek.search([
                ('state', '=', constants.SellingWeekState.INCOMING),
            ])

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
            'domain': [
                ('shipping_line_id', '=', self.shipping_line_id.id),
                ('selling_week_id', 'in', selling_weeks.ids),
                ('product_template_id.product_type', '=', constants.ProductTemplateType.SEA_FREIGHT),
                ('product_template_id.categ_id.service_type', '=', self.service_type),
            ],
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
            'domain': [
                ('categ_id.service_type', '=', self.service_type),
            ],
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
        
    def action_update_state(self):
        new_state = self.env.context.get('new_state')
        self.write({'state': new_state})

        return True

    @api.model
    def _get_client_domain(self):
        user = self.env.user
        if user.has_group('base.group_system'):
            return []
        return [('user_id', '=', user.id)]

    def action_print_quotation(self):
        """in báo giá"""
        return self.env.ref('hp_sale.action_report_quotation_hpl').report_action(self)

    @api.depends('service_type','main_transport_mode')
    def _compute_is_sea_exp_location(self):
        for record in self:
            record.is_sea_exp_location = (record.service_type == constants.ServiceType.EXPORT and record.main_transport_mode == constants.TransportMode.SEA)

    @api.onchange('exp_from_location_id', 'exp_to_location_id')
    def _onchange_exp_locations(self):
        for record in self:
            if record.service_type == constants.ServiceType.EXPORT and record.main_transport_mode == constants.TransportMode.SEA:
                if record.exp_from_location_id:
                    record.from_location_id = record.exp_from_location_id
                if record.exp_to_location_id:
                    record.to_location_id = record.exp_to_location_id

    @api.onchange('imp_from_location_id', 'imp_to_location_id')
    def _onchange_imp_locations(self):
        for record in self:
            if not (record.service_type == constants.ServiceType.EXPORT and record.main_transport_mode == constants.TransportMode.SEA):
                if record.imp_from_location_id:
                    record.from_location_id = record.imp_from_location_id
                if record.imp_to_location_id:
                    record.to_location_id = record.imp_to_location_id

    def _validate_form(self, vals):
        error_messages = []

        if 'client_id' in vals and not vals.get('client_id'):
            error_messages.append(_('Client must be specified.'))

        if 'etd' in vals:
            if not vals.get('etd'):
                error_messages.append(_('ETD must be specified.'))
            elif fields.Date.from_string(vals['etd']) < fields.Date.today():
                error_messages.append(_('ETD cannot be in the past.'))

        # Lấy ngày báo giá và ngày hết hạn từ vals hoặc dữ liệu cũ
        d_order = fields.Datetime.to_datetime(vals.get('date_order') or (self and self.date_order))
        d_valid = fields.Date.to_date(vals.get('validity_date') or (self and self.validity_date))

        if d_order and d_valid and d_valid < d_order.date():
            error_messages.append(_("Expiration date must be superior to quotation date."))

        # For existing records, combine with current values
        if self:
            # Get current values
            current_values = {
                'service_type': self.service_type,
                'main_transport_mode': self.main_transport_mode,
                'goods_location_id': self.goods_location_id.id if self.goods_location_id else False,
                'from_location_id': self.from_location_id.id if self.from_location_id else False,
                'to_location_id': self.to_location_id.id if self.to_location_id else False,
                'exp_from_location_id': self.exp_from_location_id.id if self.exp_from_location_id else False,
                'exp_to_location_id': self.exp_to_location_id.id if self.exp_to_location_id else False,
                'imp_from_location_id': self.imp_from_location_id.id if self.imp_from_location_id else False,
                'imp_to_location_id': self.imp_to_location_id.id if self.imp_to_location_id else False,
            }
            # Merge with new values
            combined_vals = {**current_values, **vals}
        else:
            combined_vals = vals


        service_type = combined_vals.get('service_type')
        main_transport_mode = combined_vals.get('main_transport_mode')

        is_sea_export = (
                service_type == constants.ServiceType.EXPORT
                and main_transport_mode == constants.TransportMode.SEA
        )
        if is_sea_export:
            goods_location = combined_vals.get('goods_location_id')
            pol = combined_vals.get('exp_from_location_id') or combined_vals.get('from_location_id')
            pod = combined_vals.get('exp_to_location_id') or combined_vals.get('to_location_id')

            if not goods_location:
                error_messages.append(_('Goods Location must be specified for Sea Export.'))

            if not pol or not pod:
                error_messages.append(_('POL and POD must be specified for Sea Export.'))

            vals['from_location_id'] = pol
            vals['to_location_id'] = pod

        elif service_type != constants.ServiceType.OTHER:
            from_location = combined_vals.get('imp_from_location_id') or combined_vals.get('from_location_id')
            to_location = combined_vals.get('imp_to_location_id') or combined_vals.get('to_location_id')

            if not from_location or not to_location:
                error_messages.append(_('From and To locations must be specified.'))

            vals['from_location_id'] = from_location
            vals['to_location_id'] = to_location

        # Use vals.get to avoid key errors
        if vals.get('from_location_id') and vals.get('from_location_id') == vals.get('to_location_id'):
            error_messages.append(_('From Location and To Location cannot be the same.'))

        if error_messages:
            raise ValidationError('\n'.join(error_messages))

        return vals

    @api.model_create_multi
    def create(self, vals_list):
        processed_vals_list = []
        for vals in vals_list:
            validated_vals = self._validate_form(vals)
            processed_vals_list.append(validated_vals)
        return super().create(processed_vals_list)

    def write(self, vals):
        for record in self:
            # Check permissions for Salesman group
            if self.env.user.has_group('sales_team.group_sale_salesman'):
                allowed_states = [
                    constants.SaleOrderState.DRAFT,
                    constants.SaleOrderState.SENT_TO_CLIENT,
                    constants.SaleOrderState.REVIEW,
                ]
                if record.state not in allowed_states:
                    raise AccessError(
                        "You are not allowed to modify the order when its state is '%s'." % record.state
                    )

            record._validate_form(vals)

        return super().write(vals)

    def action_open_freight_price_wizard(self):
        self.ensure_one()
        return {
            'name': self._generate_freight_price_wizard_title(),
            'type': 'ir.actions.act_window',
            'res_model': 'hp_sale.freight.price.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,            }
        }
    def _generate_freight_price_wizard_title(self):
        for record in self:
            if record.is_sea_exp_location:
                return f"Select Freight Price For Trip {record.goods_location_id.name} - {record.from_location_id.name} - {record.to_location_id.name}"
            return f"Select Freight Price For {record.from_location_id.name} - {record.to_location_id.name}"
