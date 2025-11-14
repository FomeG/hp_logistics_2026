from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..services.res_partner_service import ResPartnerService
from odoo.exceptions import UserError
from odoo.addons.hp_components.models import constants

class Plan(models.Model):
    _name = 'trucking_planning.plan'
    _description = 'Plan'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date asc'

    name = fields.Char(
        string="Name",
        readonly=True,
        tracking=True,
    )
    plan_type = fields.Selection([
            ('export','Export'),
            ('import','Import'),
        ], string="Plan Type",
        default='export',
        required=True,
        tracking=True
    )
    booking_bill_no = fields.Char(
        string="Booking / Bill No",
        required=True,
        tracking=True,
    )
    location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        required=True,
        string="Port Pickup / Drop",
        tracking=True,
        domain=[('type', '=', 'port')],
        help="Port pickup for export plan / Port drop for import plan"
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        domain=[('partner_main_type_id.code', '=', ResPartnerService.SHIPPING_LINE)]
    )
    # date = fields.Datetime(
    #     string='Load / Return Date',
    #     index=True,
    #     tracking=True,
    # )
    container_type = fields.Selection([
            ('dry','Dry'),
            ('cool','Cool'),
            ('ot','OT'),
            ('ft','FT')
       ], string="Container Type",
        required=True,
        tracking=True
    )
    goods_cut_off = fields.Datetime(
        string="Cut Off",
    )
    # month = fields.Integer(
    #     string='Month',
    #     compute='_compute_month_year',
    #     store=True,
    #     readonly=True,
    # )
    # year = fields.Integer(
    #     string='Year',
    #     compute='_compute_month_year',
    #     store=True,
    #     readonly=True,
    # )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        inverse_name='plan_id',
    )
    status = fields.Selection([
        (constants.PlanStatus.DRAFT, 'Draft'),
        (constants.PlanStatus.CONFIRMED, 'Confirmed'),
        (constants.PlanStatus.IN_PROGRESS, 'In Progress'),
        (constants.PlanStatus.DONE, 'Done'),
        (constants.PlanStatus.CANCEL, 'Cancelled')
    ], default='in_progress')

    total_trips = fields.Char(
        string="Total Plan Trips",
        compute='_compute_total_trips',
        store=False
    )
    has_trips = fields.Boolean(
        string="Has Trips",
        compute='_compute_has_trips',
        store=False
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking id',
        readonly=True,
    )
    @api.depends('plan_line_ids.trip_ids')
    def _compute_has_trips(self):
        for record in self:
            record.has_trips = any(line.trip_ids for line in record.plan_line_ids)

    @api.onchange('booking_bill_no')
    def _check_booking_bill_no_unique(self):
        """Check if booking/bill number already exists with detailed info"""
        for record in self:
            if record.booking_bill_no:
                # Tìm plan khác có cùng booking number
                existing = self.search([
                    ('booking_bill_no', '=', record.booking_bill_no),
                    ('id', '!=', record.id)
                ], limit=1)

                if existing:
                    # ✅ Build view URL
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    view_url = f"{base_url}/web#id={existing.id}&model=trucking_planning.plan&view_type=form"

                    # ✅ Format detailed error message
                    error_message = _(
                        "❌ Booking/Bill Number Already Exists!\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "📋 EXISTING PLAN DETAILS:\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "🔖 Booking/Bill No: %(booking)s\n"
                        "📝 Plan Name: %(name)s\n"
                        "📦 Plan Type: %(plan_type)s\n"
                        "🚢 Shipping Line: %(shipping_line)s\n"
                        "📦 Container Type: %(container_type)s\n"
                        "🏢 Port: %(port)s\n"
                        "📅 Cut Off Date: %(cut_off)s\n"
                        "🔄 Status: %(status)s\n\n"
                        "🔗 View URL:\n%(url)s\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "Please use a different booking number."
                    ) % {
                            'booking': existing.booking_bill_no,
                            'name': existing.name or 'N/A',
                            'plan_type': dict(existing._fields['plan_type'].selection).get(existing.plan_type, 'N/A'),
                            'shipping_line': existing.shipping_line_id.name if existing.shipping_line_id else 'N/A',
                            'container_type': dict(existing._fields['container_type'].selection).get(existing.container_type, 'N/A'),
                            'port': existing.location_id.name if existing.location_id else 'N/A',
                            'cut_off': existing.goods_cut_off.strftime('%Y-%m-%d %H:%M') if existing.goods_cut_off else 'N/A',
                            'status': dict(existing._fields['status'].selection).get(existing.status,'N/A'),
                            'url': view_url,
                                }
                    raise ValidationError(error_message)
    # @api.depends('date')
    # def _compute_month_year(self):
    #     for record in self:
    #         if record.date:
    #             record.month = record.date.month
    #             record.year = record.date.year
    #         else:
    #             record.month = False
    #             record.year = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                user = self.env.user
                branch = self.env['trucking_planning.branch'].search([
                    ('user_ids', 'in', [user.id]),
                ], limit=1)
                prefix = branch.plan_prefix if branch else 'PLAN'
                today = fields.Date.today().strftime('%Y%m%d')
                seq_number = self.env['ir.sequence'].next_by_code('trucking_planning.plan')
                vals['name'] = f"{prefix}/{today}/{seq_number}"

        records = super().create(vals_list)
        return records


    @api.depends('plan_line_ids')
    def _compute_total_trips(self):
        for record in self:
            record.total_trips = "0 Customer(s)"
            if record.plan_line_ids:
                record.total_trips = f"{len(record.plan_line_ids)} Customer(s)"

    def action_view_plan_lines(self):
        self.ensure_one()
        return {
            'name': 'Customer',
            'res_model': 'trucking_planning.plan.line',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {
                'default_plan_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_add_truck(self):
        """Action để thêm truck mới cho plan này"""
        self.ensure_one()
        plan_line_ids = self.plan_line_ids.ids

        if not plan_line_ids:
            raise ValidationError("Plan này chưa có customer nào. Vui lòng thêm customer trước khi add truck.")

        return {
            'name': f'Add Truck - {self.name}',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_trucking_planning.view_trip_form').id,
            'context': {
                'default_plan_id': self.id,
                'available_plan_line_ids': plan_line_ids,
                'show_plan_line_selection': True,
            },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_add_client(self):
        """Action để thêm customer mới cho plan này"""
        self.ensure_one()
        return {
            'name': f'Add Customer - {self.name}',
            'res_model': 'trucking_planning.plan.line',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_trucking_planning.view_plan_line_form').id,
            'context': {
                'default_plan_id': self.id,
                'default_status': constants.PlanLineStatus.CHECKING,
                'form_view_initial_mode': 'edit',
            },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_view_all_trips(self):
        """View all trips for this plan"""
        self.ensure_one()
        return {
            'name': f'All Trucks - {self.name}',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {
                'default_plan_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_send_message_to_all_trips(self):
        """Send message via API to all trips in this plan"""
        # Get all trips from all job
        all_trips = self.env['trucking_planning.trip']
        for plan_line in self.plan_line_ids:
            all_trips |= plan_line.trip_ids
        
        if not all_trips:
            raise UserError("No trips found in this plan to send messages to.")
        
        # Build message content for the first trip (as preview)
        first_trip = all_trips[0]
        message_content = first_trip._build_message_content()
        
        # Get driver phone number for the first trip
        driver_phone = first_trip.driver_id.phone if first_trip.driver_id and first_trip.driver_id.phone else None
        
        # Open confirmation wizard
        return {
            'name': 'Confirm Zalo Message',
            'type': 'ir.actions.act_window',
            'res_model': 'trucking_planning.zalo.confirmation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'record_id': self.id,
                'record_model': self._name,
                'message_content': message_content,
                'driver_phone': driver_phone,
            }
        }

    def action_export_plan_docx(self):
        pass # Placeholder for the new method

    # _sql_constraints = [
    #     ('unique_booking','Unique(booking_bill_no)','Booking number is unique!'),
    # ]

    def create_booking_async(self, booking_vals):
        booking = self.env['freight.purchase.booking'].with_context(skip_validator=True).create(booking_vals)
        self.write({'booking_id': booking.id})
        return booking.id

    # #todo
    # @api.model
    # def get_or_create_from_cs_order(self, cs_order):
    #     if not cs_order.booking_id:
    #         raise ValidationError("CS Order phải có Booking để tạo Plan.")
    #
    #     booking = cs_order.booking_id
    #
    #     # Tìm hoặc tạo Plan theo Booking Code
    #     plan = self.search([('booking_bill_no', '=', booking.code)], limit=1)
    #     if plan:
    #         return plan
    #
    #     # Giả lập dữ liệu (sẽ thay bằng logic thật sau)
    #     plan_vals = {
    #         'booking_bill_no': booking.code,
    #         'plan_type': 'export' if cs_order.service_type == 'export' else 'import',
    #         'location_id': booking.pol_id.id or booking.pod_id.id,  # Port
    #         'shipping_line_id': booking.shipping_line_id.id,
    #         'container_type': 'dry',  # giả lập
    #         'goods_cut_off': booking.etd or fields.Datetime.now(),
    #         'booking_id': booking.id,
    #     }
    #
    #     plan = self.create(plan_vals)
    #     return plan