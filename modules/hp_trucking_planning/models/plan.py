from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..services.res_partner_service import ResPartnerService
from odoo.exceptions import UserError

class Plan(models.Model):
    _name = 'trucking_planning.plan'
    _description = 'Plan'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'date asc'

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

    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        domain=[('partner_main_type_id.code', '=', ResPartnerService.SHIPPING_LINE)]
    )
    date = fields.Date(
        string='Load / Return Date',
        index=True,
        tracking=True,
    )
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
    month = fields.Integer(
        string='Month',
        compute='_compute_month_year',
        store=True,
        readonly=True,
    )
    year = fields.Integer(
        string='Year',
        compute='_compute_month_year',
        store=True,
        readonly=True,
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        inverse_name='plan_id',
    )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
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

    @api.depends('plan_line_ids.trip_ids')
    def _compute_has_trips(self):
        for record in self:
            record.has_trips = any(line.trip_ids for line in record.plan_line_ids)

    @api.depends('date')
    def _compute_month_year(self):
        for record in self:
            if record.date:
                record.month = record.date.month
                record.year = record.date.year
            else:
                record.month = False
                record.year = False

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
                'default_status': 'checking',
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
        driver_phone = first_trip.driver_id.phone_number if first_trip.driver_id and first_trip.driver_id.phone_number else None
        
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

    _sql_constraints = [
        ('unique_booking','Unique(booking_bill_no)','Booking number is unique!'),
    ]