import secrets

from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError, AccessError
import base64
import math
import logging
from datetime import datetime, timedelta
from ..services.planning_service import planning_service
from ..services.res_partner_service import ResPartnerService
from ...hp_components.services.partner_service import PartnerService
from odoo.addons.hp_components.models import constants

_logger = logging.getLogger(__name__)


class Trip(models.Model):
    _name = 'trucking_planning.trip'
    _description = 'Trip'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'plan_line_id'

    plan_line_id = fields.Many2one(
        comodel_name='trucking_planning.plan.line',
        string='Plan',
        required=True,
    )
    # Related fields để hiển thị thông tin Plan
    plan_id = fields.Many2one(
        comodel_name='trucking_planning.plan',
        related='plan_line_id.plan_id',
        string='Plan',
        readonly=True,
        store=True,
    )
    plan_type = fields.Selection(
        related='plan_line_id.plan_id.plan_type',
        string='Plan Type',
        readonly=True,
        store=True,
    )

    plan_booking_bill_no = fields.Char(
        related='plan_line_id.plan_id.booking_bill_no',
        string='Booking/Bill No',
        readonly=True,
        store=True,
    )
    plan_date = fields.Datetime(
        related='plan_line_id.date',
        string='Plan Date',
        readonly=True,
        store=True,
    )
    plan_shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        related='plan_line_id.plan_id.shipping_line_id',
        string='Plan Shipping Line',
        readonly=True,
        store=True,
    )
    plan_estimate_time_departure = fields.Datetime(
        related='plan_line_id.estimate_time_departure',
        string='ETD',
        readonly=True,
        store=True,
    )
    plan_estimate_time_arrival = fields.Datetime(
        related='plan_line_id.estimate_time_arrival',
        string='ETA',
        readonly=True,
        store=True,
    )

    plan_goods_pickup_location_id = fields.Many2one(
        comodel_name='location.base',
        related='plan_line_id.goods_pickup_location_id',
        string='Goods Pickup Location',
        readonly=True,
        store=True,
    )

    plan_goods_delivery_location_id = fields.Many2one(
        comodel_name='location.base',
        related='plan_line_id.goods_delivery_location_id',
        string='Goods Delivery Location',
        readonly=True,
        store=True,
    )
    route_id = fields.Many2one(
        comodel_name='route.base',
        related='plan_line_id.route_id',
        string='Route',
        readonly=True,
        store=True,
    )
    actual_source_location_id = fields.Many2one(
        comodel_name='location.base',
        related='plan_line_id.actual_source_location_id',
        string='From Location',
        readonly=True,
        store=True,
    )
    actual_destination_location_id = fields.Many2one(
        comodel_name='location.base',
        related='plan_line_id.actual_destination_location_id',
        string='To Location',
        readonly=True,
        store=True,
    )
    code = fields.Char(
        string='Job Number',
        tracking=True,
    )
    status = fields.Selection([
        (constants.TripStatus.DRAFT, 'Draft'),
        (constants.TripStatus.ON_ROUTE, 'On Route'),
        (constants.TripStatus.DONE, 'Done'),
        (constants.TripStatus.STOPPED, 'Stopped'),
        (constants.TripStatus.CANCELLED, 'Cancelled'),
    ],
        default=constants.TripStatus.DRAFT,
        string='Status',
        tracking=True,
    )
    is_admin_user = fields.Boolean(
        string='Is Admin User',
        compute='_compute_is_admin_user',
        store=False,
    )

    @api.depends_context('uid')
    def _compute_is_admin_user(self):
        for trip in self:
            trip.is_admin_user = self.env.user.has_group(
                'hp_trucking_planning.group_hp_trucking_planning_administrator')

    container_number = fields.Char(
        string="Container Number",
        tracking=True,
    )
    seal_number = fields.Char(
        string="Seal Number",
        tracking=True,
    )
    container_type = fields.Selection(
        related='plan_id.container_type',
        string='Container Type',
        readonly=True,
        store=True,
    )

    container_size = fields.Selection([
        ('20', '20'),
        ('40', '40')
    ], string="Container Size", required=True, tracking=True)

    # vehicle_driver_history_id = fields.Many2one(
    #     comodel_name='trucking_planning.vehicle.driver.history',
    #     string='Vehicle',
    #     index=True,
    # )
    vehicle_assignment_log_id = fields.Many2one(
        comodel_name='fleet.vehicle.assignation.log',
        string='Vehicle Assignment Log',
        index=True,
    )
    truck_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Truck',
        compute='_compute_truck_id',
        store=True,
        readonly=True,
    )

    driver_id = fields.Many2one(
        comodel_name='res.partner.driver',
        string='Driver',
        compute='_compute_driver_id',
        store=True,
        readonly=True,
        domain=lambda self: self._get_driver_domain()
    )

    def _get_driver_domain(self):
        return [('partner_main_type_id', '=',self.env['hp_components.partner.service'].get_partner_main_type_driver().id)]

    # truck_id = fields.Many2one(
    #     comodel_name='fleet.vehicle',
    #     related='vehicle_assignment_log_id.vehicle_id',
    #     store=True,
    #     string='Truck',
    #     index=True,
    #     tracking=True,
    # )
    # driver_id = fields.Many2one(
    #     comodel_name="res.partner.driver",
    #     related='vehicle_assignment_log_id.driver_id',
    #     store=True,
    #     string="Driver",
    #     index=True,
    #     tracking=True,
    # )
    trailer_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Trailer',
        compute='_compute_trailer_id',
        readonly=True,
        store=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner.client',
        related='plan_line_id.client_id',
        string='Client',
        readonly=True,
        store=True,
    )
    client_tax_number = fields.Char(
        related='plan_line_id.client_id.vat',
        string='Client Tax Number',
        readonly=True,
        store=True,
    )
    note = fields.Text(string="Note")
    weight_class = fields.Selection([
        ('inferior_20', '<20T'),
        ('superior_20', '>20T'),
        ('mix', 'Mix')
    ],
        required=True,
        string="Weight Class",
        tracking=True,
    )
    extra_charge = fields.Float(
        string="Extra Charge",
        tracking=True
    )
    extra_fuel = fields.Float(
        string="Extra Fuel",
        tracking=True
    )
    freeway = fields.Boolean(
        default=False,
    )
    fuel_liters = fields.Float(
        compute='_compute_fuel_liters',
        store=True,
        string="Fuel Liters",
        tracking=True,
    )
    total_cost = fields.Float(
        string="Total Cost",
        compute='_compute_total_cost',
        store=True,
        readonly=True,
        tracking=True,
    )
    # goods info
    goods_name = fields.Char(
        related='plan_line_id.goods_name',
        string="Goods Name",
        readonly=True,
        store=True,
    )
    goods_weight = fields.Float(
        related='plan_line_id.goods_weight',
        string="Goods Weight",
        readonly=True,
        store=True,
    )
    goods_cut_off = fields.Datetime(
        related='plan_id.goods_cut_off',
        string="Cut Off",
        readonly=True,
        store=True,
    )

    route_info = fields.Text(
        compute='_compute_route_info',
        store=False,
    )
    container_info = fields.Char(
        compute='_compute_container_info',
        store=False,
    )

    driver_info = fields.Text(
        compute='_compute_driver_info',
        store=False,
    )

    is_eta_near = fields.Boolean(
        string='Nearing ETA',
        compute='_compute_is_eta_near',
        store=True,
        help='True if trip ETA is within the configured threshold'
    )
    
    is_current = fields.Boolean(
        string='Current Trip',
        default=False,
        tracking=True,
        help='Indicates if this is the driver\'s current active trip for GPS tracking'
    )
    
    checkpoint_ids = fields.One2many(
        comodel_name='trucking_planning.trip_checkpoint',
        inverse_name='trip_id',
        string='GPS Checkpoints',
        help='GPS location checkpoints for this trip'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck this to archive the trip instead of deleting it'
    )
    is_external_vehicle = fields.Boolean(
        string="Rented Vehicle",
        default=False,
        tracking=True,
    )

    is_combined_vehicle = fields.Boolean(
        string="Combined Vehicle",
        default=False,
        tracking=True,
    )

    special_note = fields.Text(
        string="Special note for external/combined vehicle",
        help="Special notes when using rented or combined vehicles",
    )

    access_token = fields.Char(
        string='Access Token',
        copy=False,
        index=True,
        default=lambda self: secrets.token_urlsafe(32),
        help='Token for public access without login'
    )

    access_token_expires = fields.Datetime(
        string='Token Expires At',
        copy=False,
        help='Token expiration time (30 minutes from creation)'
    )

    def get_public_url(self):
        """
        Get public URL for trip tracking
        ✅ Auto refresh token if expired or missing
        """
        self.ensure_one()

        # ✅ Auto refresh token if:
        # - No token
        # - No expiry date
        # - Already expired
        if not self.access_token or \
                not self.access_token_expires or \
                self.access_token_expires < fields.Datetime.now():
            # Generate new token (30 minutes validity)
            self.write({
                'access_token': secrets.token_urlsafe(32),
                'access_token_expires': fields.Datetime.now() + timedelta(minutes=30)
            })

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/trip/view/{self.access_token}"

    def is_token_valid(self, token, auto_refresh=False):
        """
        Check if token is valid and not expired
        """
        self.ensure_one()

        if not self.access_token or self.access_token != token:
            if auto_refresh:
                return (False, None)
            return False

        if not self.access_token_expires:
            if auto_refresh:
                return (False, None)
            return False

        # Check if expired
        is_expired = self.access_token_expires <= fields.Datetime.now()

        if is_expired and auto_refresh:
            _logger.info(f"Token expired for trip {self.id}, auto-refreshing...")
            # Generate new token
            new_token = secrets.token_urlsafe(32)
            self.write({
                'access_token': new_token,
                'access_token_expires': fields.Datetime.now() + timedelta(minutes=30)
            })

            _logger.info(f"New token generated for trip {self.id}")
            return (True, new_token)  # Valid after refresh, return new token

        if auto_refresh:
            return (not is_expired, None)  # (valid, no new token)
        else:
            return not is_expired

    def refresh_access_token(self):
        """
        ✅ Manual refresh token (for button or scheduled action)
        Generates new token with 30 minutes validity
        """
        for trip in self:
            trip.write({
                'access_token': secrets.token_urlsafe(32),
                'access_token_expires': fields.Datetime.now() + timedelta(minutes=30)
            })

        return True


    def _set_status_via_wizard(self, new_status, note=''):
        self.ensure_one()
        from_wizard = self.env.context.get('from_wizard', False)
        from_zalo = self.env.context.get('from_zalo_driver', False)

        old_status = self.status
        vals_to_write = {'status': new_status}
        # Tự động set is_current = True khi chuyển sang ON_ROUTE
        if new_status == constants.TripStatus.ON_ROUTE and self.driver_id:
            vals_to_write['is_current'] = True
            _logger.info(f"Auto-setting is_current=True for trip {self.id} when status changed to ON_ROUTE")

        # Tự động unset is_current khi chuyển sang DONE hoặc CANCELLED
        elif new_status in [constants.TripStatus.DONE, constants.TripStatus.CANCELLED]:
            vals_to_write['is_current'] = False
            _logger.info(f"Auto-setting is_current=False for trip {self.id} when status changed to {new_status}")
        self.write(vals_to_write)

        log_body = f"Status changed from {old_status} to {new_status} lúc {fields.Datetime.now()}."
        if note:
            log_body += f"\nNote: {note}"
        if from_zalo:
            log_body += "\n(Via Zalo driver checkpoint)"
        elif from_wizard:
            log_body += "\n(Via wizard confirm)"
        self.message_post(body=log_body, message_type='notification')

        _logger.info(f"Status updated for trip {self.id}: {old_status} -> {new_status} (from={'zalo' if from_zalo else 'wizard' if from_wizard else 'direct'})")

        return True

    def action_start_trip(self):
        self.ensure_one()
        return self._open_operation_wizard(constants.TripStatus.ON_ROUTE)

    def action_mark_done(self):
        self.ensure_one()
        return self._open_operation_wizard(constants.TripStatus.DONE)

    def action_stop(self):
        self.ensure_one()
        return self._open_operation_wizard(constants.TripStatus.STOPPED)

    def action_cancel(self):
        self.ensure_one()
        return self._open_operation_wizard(constants.TripStatus.CANCELLED)

    def _open_operation_wizard(self, operation):
        return {
            'name': _(f"{operation.capitalize()} Trip"),
            'type': 'ir.actions.act_window',
            'res_model': 'trucking_planning.trip.operation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_trip_id': self.id,
                'default_operation': operation,
            },
        }
    def toggle_active(self):
        for trip in self:
            if trip.status not in [constants.TripStatus.DRAFT, constants.TripStatus.CANCELLED]:
                raise UserError("You only deleted trips when status is draft or cancelled'.")
        return super(Trip, self).toggle_active()

    @api.depends('vehicle_assignment_log_id.vehicle_id')
    def _compute_truck_id(self):
        for rec in self:
            rec.truck_id = rec.vehicle_assignment_log_id.vehicle_id if rec.vehicle_assignment_log_id else False

    @api.depends('vehicle_assignment_log_id.driver_id')
    def _compute_driver_id(self):
        for rec in self:
            if rec.vehicle_assignment_log_id and rec.vehicle_assignment_log_id.driver_id:
                driver = self.env['res.partner.driver'].search([
                    ('partner_id', '=', rec.vehicle_assignment_log_id.driver_id.id)
                ], limit=1)
                rec.driver_id = driver.id if driver else False
            else:
                rec.driver_id = False

    @api.depends('truck_id')
    def _compute_trailer_id(self):
        for trip in self:
            hpl_record = self.env['fleet.vehicle.hpl'].search([
                ('vehicle_id', '=', trip.truck_id.id)
            ], limit=1)
            trip.trailer_id = hpl_record.trailer_id if hpl_record else False

    def action_duplicate_with_queue(self):
        for trip in self:
            trip.with_delay().create_duplicated_trips()

    def create_duplicated_trips(self):
        """Queue job to create duplicated trips"""
        for trip in self:
            new_vals = {
                'plan_line_id': trip.plan_line_id.id,
                'container_size': trip.container_size,
                'weight_class': trip.weight_class,
                'freeway': trip.freeway,
                'container_number': trip.container_number,
                'seal_number': trip.seal_number,
                'note': trip.note,
                'extra_charge': trip.extra_charge,
                'extra_fuel': trip.extra_fuel,
                # reset unique fields
                'vehicle_assignment_log_id': False,
                'status': constants.TripStatus.DRAFT,
            }
            new_trip = self.create(new_vals)

            return new_trip

    def get_conflicting_trip(self, vehicle_assignment_log):
        self.ensure_one()

        if self.plan_estimate_time_departure and self.plan_estimate_time_arrival:
            time_conflict = self.search([
                ('id', '!=', self.id),
                ('vehicle_assignment_log_id', '=', vehicle_assignment_log.id),
                ('plan_estimate_time_departure', '<=', self.plan_estimate_time_arrival),
                ('plan_estimate_time_arrival', '>=', self.plan_estimate_time_departure),
                ('vehicle_assignment_log_id.date_end', '=', False),
            ], limit=1)
            if time_conflict:
                return time_conflict

        current_running_trip = self.search([
            ('vehicle_assignment_log_id', '=', vehicle_assignment_log.id),
            ('is_current', '=', True),
            ('status', '=', constants.TripStatus.ON_ROUTE),
        ], limit=1)

        if current_running_trip:
            return current_running_trip
        return False

    def process_vehicle_driver_reassignment(self):
        for trip in self:
            conflicting_trips = trip.get_conflicting_trip(trip.vehicle_assignment_log_id)
            if conflicting_trips and conflicting_trips.exists():
                for conflicting_trip in conflicting_trips:
                    conflicting_trip.vehicle_assignment_log_id = False
                    conflicting_trip.message_post(
                        body=f"Vehicle-driver pair '{self.vehicle_assignment_log_id.name}' has been unassigned and reassigned to another trip.",
                        message_type='notification'
                    )

    @api.model_create_multi
    def create(self, vals_list):
        trips = super(Trip, self).create(vals_list)

        for trip, vals in zip(trips, vals_list):
            if 'truck_id' in vals and vals['truck_id']:
                if trip.plan_line_id:
                    used_truck_ids = self.search([
                        ('plan_line_id', '=', trip.plan_line_id.id),
                        ('truck_id', '=', vals['truck_id']),
                        ('id', '!=', trip.id),
                        ('status', 'not in', [constants.TripStatus.CANCELLED]),
                    ])
                    if used_truck_ids:
                        raise ValidationError(
                            f"Truck {vals['truck_id']} is already assigned to another trip in the same customer!")

                if trip.plan_date:
                    plan_date = trip.plan_date.date() if trip.plan_date else None
                    if plan_date:
                        used_truck_ids_in_date = self.search([
                            ('plan_date', '>=',fields.Datetime.to_string(datetime.combine(plan_date, datetime.min.time()))),
                            ('plan_date', '<', fields.Datetime.to_string(datetime.combine(plan_date + timedelta(days=1), datetime.min.time()))),
                            ('truck_id', '=', vals['truck_id']),
                            ('id', '!=', trip.id),
                            ('status', 'not in', [constants.TripStatus.CANCELLED]),
                        ])
                        if used_truck_ids_in_date:
                            raise ValidationError(
                                f"Truck {vals['truck_id']} is already assigned to another trip on the same date!")

                if trip.plan_date:
                    trip.with_delay().remove_vehicle_driver_of_plan_and_plan_line(
                        vehicle_id=vals['truck_id'],
                        date_plan=trip.plan_date,
                        exclude_trip_id=trip.id
                    )

        return trips

    @api.model
    def write(self, vals):
        result = super(Trip, self).write(vals)

        if 'truck_id' in vals or 'plan_date' in vals:
            for record in self:
                if record.truck_id and record.plan_date:
                    record.with_delay().remove_vehicle_driver_of_plan_and_plan_line(
                        vehicle_id=record.truck_id.id,
                        date_plan=record.plan_date,
                        exclude_trip_id=record.id
                    )
        return result

    def remove_vehicle_driver_of_plan_and_plan_line(self, vehicle_id, date_plan, exclude_plan_id):
        planning_service(self.env).remove_vehicle_driver_by_vehicle_and_date_plan(vehicle_id, date_plan, exclude_plan_id)

    def action_view_job(self):
        """Action để xem customer (job) của trip này"""
        self.ensure_one()
        return {
            'name': f'Customer - {self.plan_line_id.code or self.plan_line_id.client_id.name}',
            'res_model': 'trucking_planning.plan.line',
            'view_mode': 'form',
            'res_id': self.plan_line_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_back_to_plan(self):
        """Navigate back to parent plan"""
        self.ensure_one()
        return {
            'name': f'Plan - {self.plan_id.name}',
            'res_model': 'trucking_planning.plan',
            'view_mode': 'form',
            'res_id': self.plan_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_view_plan_all_trips(self):
        """View all trips in the parent plan"""
        self.ensure_one()
        return {
            'name': f'All Trucks - {self.plan_id.name}',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.plan_id.id)],
            'context': {
                'default_plan_id': self.plan_id.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_open_truck_detail(self):
        self.ensure_one()
        return {
            'name': f'Truck Detail - {self.truck_id.name if self.truck_id else "New"}',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'form',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new_tab',
            'context': {
                'form_view_initial_mode': 'edit',
            }
        }

    @api.depends('plan_line_id.route_id', 'truck_id', 'weight_class', 'extra_fuel')
    def _compute_fuel_liters(self):
        for rec in self:
            if rec.plan_line_id.route_id and rec.truck_id:
                hpl_vehicle = self.env['fleet.vehicle.hpl'].search([('vehicle_id', '=', rec.truck_id.id)], limit=1)
                fuel_rate = hpl_vehicle.fuel_rate_mix if hpl_vehicle else 0.0
                if rec.weight_class == 'inferior_20':
                    fuel_rate = hpl_vehicle.fuel_rate_inferior_20 if hpl_vehicle else 0.0
                elif rec.weight_class == 'superior_20':
                    fuel_rate = hpl_vehicle.fuel_rate_superior_20 if hpl_vehicle else 0.0
                distance = rec.plan_line_id.route_id.distance_km
                if rec.plan_line_id.route_id.extra_fuel:
                    distance = rec.plan_line_id.route_id.distance_km + 40
                rec.fuel_liters = math.ceil(distance * fuel_rate * 2) + rec.extra_fuel
            else:
                rec.fuel_liters = 0.0

    @api.depends('plan_line_id.route_id', 'extra_charge')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.plan_line_id.route_id.total_cost + rec.extra_charge

    def _compute_access_url(self):
        for record in self:
            record.access_url = f'/my/trip/{record.id}'

    def action_preview_trip_order(self):
        """Preview the trip order in portal view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def _get_portal_return_action(self):
        """Return the action to return to the backend from the portal"""
        self.ensure_one()
        return self.env.ref('hp_trucking_planning.action_trip')

    def action_send_message(self):
        """Send message via API for trip"""
        # Build message content
        message_content = self._build_message_content()
        
        # Get driver phone number
        driver_phone = self.driver_id.phone if self.driver_id and self.driver_id.phone else None
        
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

    def get_route_info(self):
        """Common method to get route and location information for a trip
        Get route and location information
        IMPORT:
            - Nơi lấy cont: Port Drop (plan.location_id - port)
            - Nơi hạ công: Place of Delivery (goods_delivery_location_id)
            - Địa điểm đóng hàng: To Location (actual_destination_location_id)
            - Nơi trả vỏ: Empty Depot Pickup (container_port_location_id - depot)
        EXPORT:
            - Nơi lấy cont: Port Pickup (plan.location_id - port)
            - Nơi hạ công: Empty Depot Return (container_port_location_id - depot)
            - Địa điểm đóng hàng: Place of Pickup (goods_pickup_location_id)
            - Nơi lấy vỏ: Empty Depot Return (container_port_location_id - depot)"""

        plan_line = self.plan_line_id
        plan = plan_line.plan_id if plan_line else None

        result = {
            'booking_bill': 'N/A',
            'container_info': 'N/A',
            'shipping_line': 'N/A',
            'pickup_port': 'N/A',          # Nơi lấy cont
            'delivery_port': 'N/A',        # Nơi hạ công
            'empty_depot': 'N/A',          # Nơi trả vỏ/lấy vỏ
            'goods_weight': '',
            'loading_time': 'N/A',
            'loading_location': 'N/A',
            'contact_number': 'N/A',
            'notes': self.note or ''
        }

        # 1. Thông tin đóng trả hàng
        if plan:
            result['booking_bill'] = plan.booking_bill_no or 'N/A'

        if self.container_type or self.container_size:
            container_parts = []
            if self.container_type:
                container_parts.append(self.container_type)
            if self.container_size:
                container_parts.append(self.container_size)
            result['container_info'] = ' '.join(container_parts)

        if plan and plan.shipping_line_id:
            result['shipping_line'] = plan.shipping_line_id.name or 'N/A'

        # Fix location mapping according to user requirements
        # Nơi lấy công (Pickup Port): Always port
        # if plan and plan.location_id:
        #     result['pickup_port'] = plan.location_id.name or 'N/A'

        # Nơi hạ công (Delivery Port): Different logic for import vs export
        if plan and plan.plan_type == 'import':
            # Nơi lấy cont: Port Drop
            if plan.location_id:
                result['pickup_port'] = plan.location_id.name or 'N/A'
            # Import: Nơi hạ công = place of delivery
            location = plan_line.goods_delivery_location_id if plan_line else None
            if location:
                address = location.address or ''
                delivery_port = f"{location.name} ({address})" if address else location.name
            result['delivery_port'] = delivery_port
            # Nơi trả vỏ: Empty Depot Pickup
            if plan_line and plan_line.container_port_location_id:
                result['empty_depot'] = plan_line.container_port_location_id.name or 'N/A'
        else:
            # Nơi lấy cont: Port Pickup
            if plan.location_id:
                result['pickup_port'] = plan.location_id.name or 'N/A'
            # Nơi hạ công: Empty Depot Return
            if plan_line and plan_line.container_port_location_id:
                result['delivery_port'] = plan_line.container_port_location_id.name or 'N/A'
            # Nơi lấy vỏ: Empty Depot Return (same as delivery_port)
            if plan_line and plan_line.container_port_location_id:
                result['empty_depot'] = plan_line.container_port_location_id.name or 'N/A'
            # # Export: Nơi hạ công = same port
            # result['delivery_port'] = plan.location_id.name if plan and plan.location_id else 'N/A'

        if plan_line and plan_line.goods_weight:
            result['goods_weight'] = f"{plan_line.goods_weight} Tấn"

        # 2. Đóng hàng/ Hạ Hàng
        if plan_line and plan_line.date:
            user_tz = self.env.user.tz or 'Asia/Ho_Chi_Minh'
            localized_date = fields.Datetime.context_timestamp(self, plan_line.date)
            result['loading_time'] = localized_date.strftime("%d/%m/%Y %H:%M")
        loading_location = None
        contact_number = ''

        # Địa điểm đóng hàng (Loading Address): Different logic for import vs export
        # Import: Địa điểm đóng hàng = address của to location (trong route)
        if plan and plan.plan_type == 'import':
            location = plan_line.actual_destination_location_id if plan_line else None
            if location:
                address = location.address or ''
                loading_location = f"{location.name} ({address})" if address else location.name
                contact_number = location.contact_phone or ''
        # Export: Địa điểm đóng hàng = place of pickup address
        else:
            location = plan_line.goods_pickup_location_id if plan_line else None
            if location:
                address = location.address or ''
                loading_location = f"{location.name} ({address})" if address else location.name
                contact_number = location.contact_phone or ''

        result['loading_location'] = loading_location
        result['contact_number'] = contact_number

        return result

    def _build_message_content(self):
        """Build the message content for trip"""
        route_info = self.get_route_info()
        plan = self.plan_line_id.plan_id if self.plan_line_id else None
        section_title = "Đóng hàng" if plan and plan.plan_type == 'import' else "Hạ hàng"
        if plan and plan.plan_type == 'import':
            depot_label = "Nơi trả vỏ"  # Empty Depot Pickup
        else:
            depot_label = "Nơi lấy vỏ"  # Empty Depot Return
        message = f"""1. Thông tin đóng trả hàng:

        Số booking/số bill: {route_info['booking_bill']}
        Loại container: {route_info['container_info']} - hãng tầu ({route_info['shipping_line']})
        Nơi lấy Cont: {route_info['pickup_port']}
        Nơi hạ cont: {route_info['delivery_port']}
        {depot_label}: {route_info['empty_depot']}
        Trọng lượng hàng: {route_info['goods_weight']}

2. {section_title}:

        Thời gian đóng hàng: {route_info['loading_time']}
        Địa điểm đóng hàng: {route_info['loading_location']}
        Số liên hệ: {route_info['contact_number']}"""

        if route_info['notes'] and route_info['notes'].strip():
            message += f"""

3. Các Yêu Cầu khác:

        Notes: {route_info['notes'].strip()}"""

        return message

    def action_send_message_bulk(self):
        """Send message via API for multiple selected trips"""
        if not self:
            raise UserError("No trips selected to send messages to.")
        
        # Build message content for the first trip (as preview)
        first_trip = self[0]
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
                'record_id': first_trip.id,  # Use first trip as representative
                'record_model': 'trucking_planning.trip.bulk',  # Special model for bulk
                'message_content': message_content,
                'driver_phone': driver_phone, # Use first trip phone
                'bulk_trip_ids': self.ids,  # Pass all trip IDs
            }
        }

    def action_export_trip_docx(self):
        """Export trip data to DOCX format matching the transport document"""
        return self.env['hp.document.service.trucking'].generate_docx(self)

    def action_export_trip_docx_bulk(self):
        """Export selected trips to DOCX and return a ZIP download"""
        if not self:
            raise UserError("No trips selected to export.")

        import io
        import zipfile
        import base64
        import re

        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for trip in self:
                try:
                    # Generate DOCX
                    from docx import Document
                    doc = self.env['hp.document.service.trucking']._get_docx_document()
                    self.env['hp.document.service.trucking']._add_docx_header(doc, trip)
                    self.env['hp.document.service.trucking']._add_docx_body(doc, trip)
                    self.env['hp.document.service.trucking']._add_docx_footer(doc, trip)

                    # Save document to bytes
                    doc_io = io.BytesIO()
                    doc.save(doc_io)
                    doc_io.seek(0)

                    # Build safe filename, mirroring single export
                    driver_name = trip.driver_id.name if trip.driver_id else 'N/A'
                    safe_driver_name = re.sub(r'[^\w\s-]', '', driver_name).strip() if driver_name != 'N/A' else 'TaiXe'
                    safe_driver_name = re.sub(r'[-\s]+', '_', safe_driver_name)
                    trip_date = trip.plan_line_id.date if trip.plan_line_id else fields.Datetime.now()
                    if isinstance(trip_date, datetime):
                        filename = f"GiayVanTai_{safe_driver_name}_{trip_date.strftime('%d_%m_%Y')}.docx"
                    else:
                        filename = f"GiayVanTai_{safe_driver_name}_{trip_date.date().strftime('%d_%m_%Y')}.docx"

                    # Write into ZIP
                    zipf.writestr(filename, doc_io.getvalue())

                except Exception as e:
                    _logger.error(f"Error exporting trip {trip.id}: {str(e)}")
                    continue

        zip_io.seek(0)

        zip_filename = f"Trips_Export_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        attachment = self.env['ir.attachment'].create({
            'name': zip_filename,
            'type': 'binary',
            'datas': base64.b64encode(zip_io.getvalue()),
            'mimetype': 'application/zip'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _compute_route_info(self):
        for trip in self:
            freeway_text = '(freeway)' if trip.freeway else ''
            trip.route_info = f"{trip.actual_source_location_id.name} - {trip.actual_destination_location_id.name} {freeway_text}"

    def _compute_container_info(self):
        for trip in self:
            trip.container_info = f"{trip.container_type},{trip.container_size}"

    def _compute_driver_info(self):
        for trip in self:
            trip.driver_info = f"{trip.driver_id.name},{trip.truck_id.name}"

    @api.depends('plan_estimate_time_arrival', 'status')
    def _compute_is_eta_near(self):
        """Compute if trip ETA is within the configured threshold"""
        # Get the threshold from system parameter
        eta_threshold_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'hp_trucking_planning.eta_near_days', '3'
        ))
        
        now = fields.Datetime.now()
        threshold_datetime = now + timedelta(days=eta_threshold_days)
        
        for trip in self:
            # Only consider active trips (not cancelled or done)
            if trip.status in [constants.TripStatus.CANCELLED, constants.TripStatus.DONE]:
                trip.is_eta_near = False
                continue
                
            # Check if ETA is within threshold
            if trip.plan_estimate_time_arrival:
                trip.is_eta_near = (
                    now <= trip.plan_estimate_time_arrival <= threshold_datetime
                )
            else:
                trip.is_eta_near = False

    def action_open_vehicle_driver_pair_popup(self):
        self.ensure_one()
        return {
            'name': 'Select Driver–Vehicle Pair',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.assignation.log',
            'view_mode': 'list,form',
            'target': 'new',
            'context': {
                'trip_id': self.id,
            },
            "domain": [("date_end", "=", False)],
        }
    
    def _cancel_inactive_trip(self):
        planning_service(self.env).update_trip_statuses(constants.TripStatus.CANCELLED)
    
    # def _close_done_trip(self):
    #     planning_service(self.env).update_trip_statuses('done')
    
    @api.model
    def recompute_eta_near_status(self):
        """Recompute is_eta_near field for all trips when system parameter changes"""
        trips = self.search([])
        trips._compute_is_eta_near()
        return True

    @api.model
    def write(self, vals):
        """Override write to automatically unset other current trips when setting one as current"""
        result = super().write(vals)
        
        # If is_current is being set to True, unset other trips for the same driver
        if vals.get('is_current') is True:
            for trip in self:
                if trip.driver_id:
                    # Find other current trips for the same driver and unset them
                    other_current_trips = self.search([
                        ('id', '!=', trip.id),
                        ('driver_id', '=', trip.driver_id.id),
                        ('is_current', '=', True),
                        ('status', 'not in', [constants.TripStatus.DONE, constants.TripStatus.CANCELLED])
                    ])
                    if other_current_trips:
                        other_current_trips.write({'is_current': False})
                        _logger.info(f"Auto-unset {len(other_current_trips)} other current trips for driver {trip.driver_id.name}")
        
        return result


    def action_view_checkpoints(self):
        """View all GPS checkpoints for this trip"""
        self.ensure_one()
        return {
            'name': f'GPS Checkpoints - {self.code or f"Trip {self.id}"}',
            'res_model': 'trucking_planning.trip_checkpoint',
            'view_mode': 'list,form',
            'domain': [('trip_id', '=', self.id)],
            'context': {
                'default_trip_id': self.id,
                'search_default_trip_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'inline',
        }

    # @api.model
    # def get_or_create_draft_from_container(self, container, plan_line):
    #     trip = self.search([
    #         ('plan_line_id', '=', plan_line.id),
    #         ('container_number', '=', container.container_number)
    #     ], limit=1)
    #
    #     if trip:
    #         return trip
    #
    #     trip_vals = {
    #         'plan_line_id': plan_line.id,
    #         'container_number': container.container_number,
    #         'seal_number': container.seal_number,
    #         'container_size': '40' if '40' in (container.container_type_id.name or '') else '20',
    #         'status': constants.TripStatus.DRAFT,
    #     }
    #     trip = self.create(trip_vals)
    #     return trip
    #
    # @api.model
    # def get_or_create_draft_from_job(self, cs_job, plan_line):
    #     """Tạo 1 draft trip nếu chưa có container cụ thể"""
    #     if self.search([('plan_line_id', '=', plan_line.id)], limit=1):
    #         return
    #
    #     trip_vals = {
    #         'plan_line_id': plan_line.id,
    #         'container_size': '40',
    #         'status': constants.TripStatus.DRAFT,
    #     }
    #     self.create(trip_vals)