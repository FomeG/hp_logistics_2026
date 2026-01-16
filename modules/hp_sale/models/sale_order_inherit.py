from datetime import timedelta
from logging import Logger
from odoo import models, fields, _, api
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError, AccessError
from ...hp_components.models import constants
from ...hp_components.services.activity_service import ActivityService
import logging
from odoo.tools import ormcache

_logger: Logger = logging.getLogger(__name__)

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[
        (constants.SaleOrderState.DRAFT, 'Draft'),
        (constants.SaleOrderState.ACTIVE, 'Active'),
        (constants.SaleOrderState.SENT_TO_CLIENT, 'Sent To Client'),
        (constants.SaleOrderState.REVIEW, 'Review'),
        (constants.SaleOrderState.REQUEST_TO_APPROVAL, 'Request to Approval'),
        (constants.SaleOrderState.REQUEST_BOOKING, 'Request Booking'),
        (constants.SaleOrderState.DENIED, 'Denied'),
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
        # default=constants.ServiceType.EXPORT,
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
        domain=[('is_active', '=', True)],
    )
    allow_from_location_ids = fields.Many2many('location.base', compute='_compute_allow_from_location_ids', store=False)
    allow_to_location_ids = fields.Many2many('location.base', compute='_compute_allow_to_location_ids', store=False)
    department_id = fields.Many2one('hr.department', compute='_compute_department_id', store=True)

    # Computed field for filtering quotations from departments managed by current user
    is_from_managed_department = fields.Boolean(
        string='From Managed Department',
        compute='_compute_is_from_managed_department',
        search='_search_is_from_managed_department',
        store=False,
    )

    task_count = fields.Integer(
        string='Task Count',
        compute='_compute_task_count',
        store=False,
    )

    def _get_related_task_ids(self):
        self.ensure_one()
        task_ids = []

        if 'cs.order' in self.env:
            cs_orders = self.env['cs.order'].search([('sale_order_id', '=', self.id)])
            for cs_order in cs_orders:
                if cs_order.project_id:
                    tasks = self.env['project.task'].search([
                        ('project_id', '=', cs_order.project_id.id)
                    ])
                    task_ids.extend(tasks.ids)

        return task_ids

    def _compute_task_count(self):
        for order in self:
            order.task_count = len(order._get_related_task_ids())

    def action_view_tasks(self):
        """Open tasks linked to this sale order via CS Orders."""
        self.ensure_one()
        task_ids = self._get_related_task_ids()

        return {
            'name': _('Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', task_ids)],
            'context': {
                'create': False,
            },
        }

    @api.depends('user_id')
    def _compute_department_id(self):
        for rec in self:
            employee = self.env['hr.employee'].search([('user_id', '=', rec.user_id.id)], limit=1)
            rec.department_id = employee.department_id.id if employee else False


    #region quotation filter
    def _compute_is_from_managed_department(self):
        """Compute if quotation's salesperson belongs to departments managed by current user"""
        current_user = self.env.user
        managed_user_ids = self._get_managed_department_user_ids(current_user)
        for rec in self:
            rec.is_from_managed_department = rec.user_id.id in managed_user_ids

    def _search_is_from_managed_department(self, operator, value):
        """Search method for is_from_managed_department field"""
        # Admin users: match all records
        if self.env.user.has_group('base.group_system'):
            if (operator == '=' and value) or (operator == '!=' and not value):
                return [(1, '=', 1)]  # Always true - match all
            else:
                return [(1, '=', 0)]  # Always false - match none

        current_user = self.env.user
        managed_user_ids = self._get_managed_department_user_ids(current_user)

        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('user_id', 'in', managed_user_ids)]
        else:
            return [('user_id', 'not in', managed_user_ids)]

    # @api.model
    # def _get_managed_department_user_ids(self, user):
    #     """
    #     Get user IDs from all departments managed by the given user.
    #     A user can manage multiple departments.
    #     Returns list of user IDs (including the manager themselves).
    #     """
    #     # Find employee record for the given user
    #     employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
    #     if not employee:
    #         return [user.id]

    #     # Find all departments where this employee is the manager
    #     managed_departments = self.env['hr.department'].sudo().search([
    #         ('manager_id', '=', employee.id)
    #     ])

    #     if not managed_departments:
    #         return [user.id]

    #     # Get all employees from these departments
    #     employees_in_managed_depts = self.env['hr.employee'].sudo().search([
    #         ('department_id', 'in', managed_departments.ids),
    #         ('user_id', '!=', False)
    #     ])

    #     # Get user IDs from these employees
    #     user_ids = employees_in_managed_depts.mapped('user_id').ids

    #     # Always include the current user
    #     if user.id not in user_ids:
    #         user_ids.append(user.id)

    #     return user_ids
    

    @api.model
    @ormcache('user.id')
    def _get_managed_department_user_ids(self, user):
        employee = self.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        if not employee:
            return (user.id,)

        managed_departments = self.env['hr.department'].sudo().search([
            ('manager_id', '=', employee.id)
        ])

        if not managed_departments:
            return (user.id,)

        employees = self.env['hr.employee'].sudo().search([
            ('department_id', 'in', managed_departments.ids),
            ('user_id', '!=', False)
        ])

        user_ids = employees.mapped('user_id').ids
        if user.id not in user_ids:
            user_ids.append(user.id)

        return tuple(user_ids)

        
    
    @api.model
    def action_quotations_with_dynamic_filter(self):
        """
        Return quotations action with dynamic context based on user group.
        - Admin (base.group_system): No default filter - show all
        - DOS (sale leader): Show 'My Department's Quotations' filter by default
        - Others: Show 'My Quotations' filter by default
        """
        action = self.env['ir.actions.act_window']._for_xml_id('sale.action_quotations_with_onboarding')

        # Admin users: no default filter
        if self.env.user.has_group('base.group_system'):
            action['context'] = {}
            return action

        user_service = self.env['hp_components.user.service']

        # Check if user is a sale leader (DOS)
        if user_service.is_salesman_leader():
            action['context'] = {'search_default_my_department_quotations': 1}
        else:
            action['context'] = {'search_default_my_quotation': 1}

        return action

    #endregion





    @api.depends('service_type', 'main_transport_mode')
    def _compute_allow_from_location_ids(self):
        for rec in self:
            domain = []
            if rec.service_type == constants.ServiceType.EXPORT and rec.main_transport_mode == constants.TransportMode.SEA:
                domain = [('is_local', '=', True)]
            rec.allow_from_location_ids = self.env['location.base'].search(domain)

    @api.depends('service_type', 'main_transport_mode')
    def _compute_allow_to_location_ids(self):
        for rec in self:
            domain = []
            if rec.service_type == constants.ServiceType.EXPORT and rec.main_transport_mode == constants.TransportMode.SEA:
                domain = [('is_local', '=', False)]
            rec.allow_to_location_ids = self.env['location.base'].search(domain)


    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency ',
        required=True,
        default=lambda self: self.env['res.currency'].get_base_currency(),
        tracking=True,
        readonly=False,
        help='Currency for this order'
    )

    ref_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')], limit=1),
        help="Chọn đồng tiền ngoại tệ bạn muốn cấu hình tỷ giá (VD: USD)"
    )

    currency_rate_ref_id = fields.Many2one(
        comodel_name='res.currency.rate',
        string='Exchange Rate Ref',
        domain="[('currency_id', '=', ref_currency_id), ('company_id', 'in', (False, company_id))]",
        help='Select specific exchange rate record from system'
    )

    # Tỷ giá quy đổi từ currency_id -> Base Currency (is_base_currency)
    currency_rate = fields.Float(
        string='Exchange Rate',
        compute='_compute_currency_rate',
        store=True,
        digits=(12, 6),
        help='Exchange rate to the configured Base Currency'
    )

    manual_currency_rate = fields.Float(
        string='Manual Exchange Rate',
        digits=(12, 6),
        tracking=True,
        help='Override automatic exchange rate with manual rate'
    )

    use_manual_rate = fields.Boolean(
        string='Use Manual Rate',
        default=False,
        tracking=True,
    )

    currency_display_info = fields.Char(
        string='Currency Info',
        compute='_compute_currency_display_info',
        store=False
    )

    @api.onchange('service_type')
    def _onchange_service_type_set_pricelist(self):
        if not self.service_type:
            return

        # Lấy pricelist tương ứng với service_type
        xml_id = constants.SERVICE_TYPE_PRICELIST_MAP.get(self.service_type)
        if xml_id:
            pricelist = self.env.ref(xml_id, raise_if_not_found=False)
            if pricelist:
                self.pricelist_id = pricelist.id
                # Cập nhật lại giá
                if self.order_line:
                    self.order_line._onchange_product_id_set_price_from_pricelist()


    def _convert_to_order_currency(self, amount, from_currency):
        """ chuyển đổi một số tiền từ tiền tệ bất kỳ về tiền tệ của Sale Order. Sử dụng ngày của đơn hàng và company của đơn hàng."""
        self.ensure_one()
        if not from_currency or from_currency == self.currency_id:
            return amount

        return from_currency._convert(
            amount,
            self.currency_id,
            self.company_id or self.env.company,
            self.date_order or fields.Date.today()
        )

    @api.depends('ref_currency_id', 'use_manual_rate', 'manual_currency_rate', 'currency_rate_ref_id', 'date_order')
    def _compute_currency_rate(self):
        """Quy đổi 1 đơn vị của Order Currency -> Base Currency"""
        base_currency = self.env['res.currency'].get_base_currency()

        for order in self:
            # Case 1: Nhập tay (Manual)
            if order.use_manual_rate and order.manual_currency_rate:
                order.currency_rate = order.manual_currency_rate

            elif order.ref_currency_id:
                # Nếu tiền đơn hàng trùng với tiền Base => Tỷ giá 1.0
                if order.ref_currency_id == base_currency:
                    order.currency_rate = 1.0
                else:
                    # Case 2: Chọn record tỷ giá
                    if order.currency_rate_ref_id:
                        # Odoo lưu tỷ giá dạng (1 Base Company = X Foreign) -> Nghịch đảo để lấy giá trị Base
                        rate_val = order.currency_rate_ref_id.rate
                        order.currency_rate = 1.0 / rate_val if rate_val else 1.0
                    else:
                        # Case 3: Tự động lấy theo ngày
                        date_val = order.date_order.date() if order.date_order else fields.Date.today()
                        company = order.company_id or self.env.company
                        try:
                            # Quy đổi 1.0 Ref Currency -> Base Currency
                            order.currency_rate = order.ref_currency_id._convert(
                                1.0, base_currency, company, date_val
                            )
                        except Exception:
                            order.currency_rate = 1.0
            else:
                order.currency_rate = 1.0

    @api.depends('ref_currency_id', 'currency_rate', 'use_manual_rate', 'currency_rate_ref_id')
    def _compute_currency_display_info(self):
        """Hiển thị thông tin tỷ giá so với Base Currency"""
        base_currency = self.env['res.currency'].get_base_currency()
        base_code = base_currency.name or 'Base'

        for order in self:
            if order.ref_currency_id:
                rate_source = "(Auto)"
                if order.use_manual_rate:
                    rate_source = "(Manual)"
                elif order.currency_rate_ref_id:
                    date_str = order.currency_rate_ref_id.name or str(order.currency_rate_ref_id.date)
                    rate_source = f"(Selected - {date_str})"

                curr_code = order.ref_currency_id.name
                rate = order.currency_rate or 0.0

                # Format hiển thị (VD: 1 USD = 25,000.00 VND)
                rate_str = f"{rate:,.6f}" if 0 < rate < 1 else f"{rate:,.2f}"
                order.currency_display_info = f"1 {curr_code} = {rate_str} {base_code} {rate_source}"
            else:
                order.currency_display_info = ""

    @api.onchange('use_manual_rate')
    def _onchange_use_manual_rate(self):
        if not self.use_manual_rate:
            self.manual_currency_rate = 0.0

    def convert_amount_to_base(self, amount):
        """Convert số tiền từ Order Currency sang Base Currency"""
        self.ensure_one()
        return amount * (self.currency_rate or 1.0)

    def convert_amount_from_base(self, amount):
        """Convert số tiền từ Base Currency sang Order Currency"""
        self.ensure_one()
        rate = self.currency_rate or 1.0
        if rate == 0:
            return 0.0
        return amount / rate



    @api.onchange("client_id")
    def _onchange_client_id(self):
        if self.client_id and self.client_id.partner_id:
            self.partner_id = self.client_id.partner_id.id if self.client_id else False
        else:
            self.partner_id = False
        # Cập nhật pricelist theo service type
        self._onchange_service_type_set_pricelist()


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
        self.ensure_one()
        # danh sách tên Tag luôn được phép chọn
        allowed_tag_names = list(constants.DEFAULT_NORMAL_PRODUCT_TAGS)
        # thêm các Tag tương ứng với service_type của Sale Order
        additional_tags = constants.SERVICE_TYPE_TO_TAG_MAP.get(self.service_type, [])
        allowed_tag_names.extend(additional_tags)

        tag_ids = self.env['product.tag'].search([('name', 'in', allowed_tag_names)]).ids

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
                ('product_tag_ids', 'in', tag_ids),
                ('product_type', 'in', [constants.ProductTemplateType.CUSTOM, constants.ProductTemplateType.SERVICES])
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
        user_service = self.env['hp_components.user.service']
        for record in self:
            # Check permissions for Salesman group
            if (
                user_service.is_salesman_member()
                and not user_service.is_salesman_leader()
                and not user_service.is_salesman_manager()
            ):
                allowed_states = [
                    constants.SaleOrderState.DRAFT,
                    constants.SaleOrderState.ACTIVE,
                    constants.SaleOrderState.SENT_TO_CLIENT,
                    constants.SaleOrderState.REVIEW,
                    constants.SaleOrderState.REQUEST_TO_APPROVAL,
                ]
                if record.state not in allowed_states:
                    # Allow setting cancelled orders back to quotation (draft or review)
                    is_resetting_cancelled_order = (
                        vals.get('state') in [constants.SaleOrderState.DRAFT, constants.SaleOrderState.REVIEW]
                        and record.state in ['cancel', constants.SaleOrderState.CANCELLED]
                    )
                    if not is_resetting_cancelled_order:
                        raise AccessError(
                            "You are not allowed to modify the order when its state is '%s'." % record.state
                        )

            record._validate_form(vals)

        if 'state' in vals and len(self) == 1:
            ctx = dict(self.env.context)
            ctx['old_state'] = self.state
            return super(SaleOrderInherit, self.with_context(ctx)).write(vals)

        return super().write(vals)

    def action_draft(self):
        """Override: set state to 'review' if has SO lines, else 'draft'."""
        for order in self.filtered(lambda s: s.state in ['cancel', 'cancelled', 'sent']):
            order.write({'state': 'review' if order.order_line else 'draft'})
        return True

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


    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrderInherit, self).default_get(fields_list)

        # Logic này chỉ chạy khi tạo form mới
        if 'service_type' in fields_list:
            res['service_type'] = constants.ServiceType.EXPORT

        return res
    def _handle_notify(self):
        if not self.partner_id or not self.partner_id.user_id:
            return False

        service = ActivityService(
            env=self.env,
            model_name='sale.order',
            record_id=self.id,
            user_ids=self.partner_id.user_id.id
        )

        if self.state == constants.SaleOrderState.REQUEST_BOOKING:
            summary = f"Quotation {self.name} is approved and is waiting for booking."
        elif self.state == constants.SaleOrderState.DENIED:
            summary = f"Quotation {self.name} has been denied."
        else:
            return False

        service._create_activity_by_type(
            summary=summary,
            note=''
        )

        return True
