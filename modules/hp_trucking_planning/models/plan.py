from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ...hp_components.services.department_service import DepartmentService
from ..services.planning_service import planning_service
from ..services.zalo_service import ZaloService
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
        domain=[('type', '=', 'route_point')],
    )
    shipping_line_id = fields.Many2one(
        comodel_name='trucking_planning.shipping_line',
        required=True,
    )
    date = fields.Date(
        string='Load / Return Date',
        required=True,
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

    estimate_time_departure = fields.Datetime(
        string="ETD (Estimated Time of Departure)",
        required=True,
        tracking=True,
    )
    estimate_time_arrival = fields.Datetime(
        string="ETA (Estimated Time of Arrival)",
        required=True,
        tracking=True,
    )

    estimate_time_duration = fields.Float(
        string="Estimated Time Duration (Hours)",
        compute='_compute_estimate_time_duration',
        store=True,
    )

    goods_pickup_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        string="Goods Pickup Location",
        required="True",
        tracking=True,
        domain=[('type', '=', 'goods_pickup_delivery')],
        help="Location where goods will be picked up"
    )

    goods_delivery_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        string="Goods Delivery Location",
        required="True",
        tracking=True,
        domain=[('type', '=', 'goods_pickup_delivery')],
        help="Location where goods will be delivered"
    )
    @api.constrains('estimate_time_departure', 'estimate_time_arrival')
    def _check_estimate_time(self):
        for record in self:
            if record.estimate_time_departure and record.estimate_time_arrival:
                if record.estimate_time_arrival < record.estimate_time_departure:
                    raise ValidationError("Estimated Time of Arrival cannot be earlier than Estimated Time of Departure.")

    @api.depends('estimate_time_departure', 'estimate_time_arrival')
    def _compute_estimate_time_duration(self):
        for rec in self:
            if rec.estimate_time_departure and rec.estimate_time_arrival:
                delta = rec.estimate_time_arrival - rec.estimate_time_departure
                rec.estimate_time_duration = delta.total_seconds() / 3600.0
            else:
                rec.estimate_time_duration = 0.0
    # @api.model
    # def _get_vehicle_avaliable(self):
    #     domain = [
    #         ('type', '=', 'truck'),
    #     ]
    #
    #     branches = self.env['trucking_planning.branch'].sudo().search([('user_ids', 'in', [self.env.uid])])
    #     if branches:
    #         domain.append(('branch_id', 'in', [False] + branches.ids))
    #     else:
    #         domain.append(('branch_id', '=', False))
    #
    #     return domain

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
        # for record in records:
        #     if record.vehicle_id and record.date:
        #         record.with_delay().remove_vehicle_driver_of_plan_and_plan_line(
        #             vehicle_id=record.vehicle_id.id,
        #             date_plan=record.date,
        #             exclude_plan_id=record.id
        #         )
    
        return records
    
    def write(self, vals):
        result = super().write(vals)

        # if 'vehicle_id' in vals or 'date' in vals:
        #     for record in self:
        #         if record.vehicle_id and record.date:
        #             record.with_delay().remove_vehicle_driver_of_plan_and_plan_line(
        #                 vehicle_id=record.vehicle_id.id,
        #                 date_plan=record.date,
        #                 exclude_plan_id=record.id
        #             )
    
        return result

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

    # def remove_vehicle_driver_of_plan_and_plan_line(self, vehicle_id, date_plan, exclude_plan_id):
    #     planning_service(self.env).remove_vehicle_driver_by_vehicle_and_date_plan(vehicle_id, date_plan, exclude_plan_id)

    def action_send_message_to_all_trips(self):
        """Send message via API to all trips in this plan"""
        # Get all trips from all plan lines
        all_trips = self.env['trucking_planning.trip']
        for plan_line in self.plan_line_ids:
            all_trips |= plan_line.trip_ids
        
        if not all_trips:
            raise UserError("No trips found in this plan to send messages to.")
        
        # Use Zalo service to send bulk messages
        return self.env['zalo.service'].send_bulk_messages(all_trips)

    def action_export_plan_docx(self):
        pass # Placeholder for the new method

    _sql_constraints = [
        ('unique_booking','Unique(booking_bill_no)','Booking number is unique!'),
    ]