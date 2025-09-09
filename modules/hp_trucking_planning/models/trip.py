from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
import base64
import math
from datetime import datetime, timedelta
from ..services.planning_service import planning_service


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
    plan_date = fields.Date(
        related='plan_line_id.plan_id.date',
        string='Plan Date',
        readonly=True,
        store=True,
    )
    plan_shipping_line_id = fields.Many2one(
        comodel_name='trucking_planning.shipping_line',
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
        comodel_name='trucking_planning.location',
        related='plan_line_id.goods_pickup_location_id',
        string='Goods Pickup Location',
        readonly=True,
        store=True,
    )

    plan_goods_delivery_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        related='plan_line_id.goods_delivery_location_id',
        string='Goods Delivery Location',
        readonly=True,
        store=True,
    )
    client_id = fields.Many2one(
        comodel_name='trucking_planning.client',
        related='plan_line_id.client_id',
        string='Client',
        readonly=True,
        store=True,
    )
    route_id = fields.Many2one(
        comodel_name='trucking_planning.route',
        related='plan_line_id.route_id',
        string='Route',
        readonly=True,
        store=True,
    )
    actual_source_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        related='plan_line_id.actual_source_location_id',
        string='From Location',
        readonly=True,
        store=True,
    )
    actual_destination_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
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
        ('draft', 'Draft'),
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('checking', 'Checking'),
        ('done', 'Done'),
    ],
        default='draft',
        string='Status',
        tracking=True,
    )
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

    vehicle_driver_history_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle.driver.history',
        string='Vehicle',
        index=True,
    )
    truck_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        related='vehicle_driver_history_id.vehicle_id',
        store=True,
        string='Truck',
        index=True,
        tracking=True,
    )
    driver_id = fields.Many2one(
        comodel_name="trucking_planning.driver",
        related='vehicle_driver_history_id.driver_id',
        store=True,
        string="Driver",
        index=True,
        tracking=True,
    )
    trailer_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain=[('type', '=', 'trailer')],
        related='truck_id.trailer_id',
        readonly=True,
        store=True,
    )
    client_id = fields.Many2one(
        comodel_name='trucking_planning.client',
        related='plan_line_id.client_id',
        string='Client',
        readonly=True,
        store=True,
    )
    client_tax_number = fields.Char(
        related='plan_line_id.client_id.tax_number',
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
                'vehicle_driver_history_id': False,
                'status': 'draft',
            }
            new_trip = self.create(new_vals)

            return new_trip

    def get_conflicting_trip(self, vehicle_driver_history):
        if not self or not self.plan_estimate_time_departure or not self.plan_estimate_time_arrival:
            return self.browse()

        domain = [
            ("id", "!=", self.id),
            ("vehicle_driver_history_id", "=", vehicle_driver_history.id),
            ("plan_estimate_time_departure", "<=", self.plan_estimate_time_arrival),
            ("plan_estimate_time_arrival", ">=", self.plan_estimate_time_departure),
            ("vehicle_driver_history_id.end_date", "=", False),
        ]

        return self.search(domain)

    def process_vehicle_driver_reassignment(self):
        for trip in self:
            conflicting_trips = trip.get_conflicting_trip(trip.vehicle_driver_history_id)
            if conflicting_trips and conflicting_trips.exists():
                for conflicting_trip in conflicting_trips:
                    conflicting_trip.vehicle_driver_history_id = False
                    conflicting_trip.message_post(
                        body=f"Vehicle-driver pair '{self.vehicle_driver_history_id.name}' has been unassigned and reassigned to another trip.",
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
                        ('status', 'not in', ['cancelled']),
                    ])
                    if used_truck_ids:
                        raise ValidationError(
                            f"Truck {vals['truck_id']} is already assigned to another trip in the same customer!")

                if trip.plan_date:
                    used_truck_ids_in_date = self.search([
                        ('plan_date', '=', trip.plan_date),
                        ('truck_id', '=', vals['truck_id']),
                        ('id', '!=', trip.id),
                        ('status', 'not in', ['cancelled']),
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
    @api.depends('plan_line_id.route_id', 'truck_id', 'weight_class', 'extra_fuel')
    def _compute_fuel_liters(self):
        for rec in self:
            if rec.plan_line_id.route_id and rec.truck_id:
                fuel_rate = rec.truck_id.fuel_rate_mix
                if rec.weight_class == 'inferior_20':
                    fuel_rate = rec.truck_id.fuel_rate_inferior_20
                elif rec.weight_class == 'superior_20':
                    fuel_rate = rec.truck_id.fuel_rate_superior_20
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
        driver_phone = self.driver_id.phone_number if self.driver_id and self.driver_id.phone_number else None
        
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
    
    def _build_message_content(self):
        """Build the message content for trip"""
        plan_line = self.plan_line_id
        plan = plan_line.plan_id if plan_line else None
        
        # 1. Thông tin đóng trả hàng
        booking_bill = plan.booking_bill_no if plan else "N/A"
        container_info = ""
        if self.container_type:
            container_info = f"{self.container_type}"
        if self.container_size:
            container_info += f" {self.container_size}"
        if not container_info:
            container_info = "N/A"
            
        shipping_line = plan.shipping_line_id.name if plan and plan.shipping_line_id else "N/A"
        
        # Fix location mapping according to user requirements
        # Nơi lấy công (Pickup Port): Always port
        pickup_port = plan.location_id.name if plan and plan.location_id else "N/A"
        
        # Nơi hạ công (Delivery Port): Different logic for import vs export
        if plan and plan.plan_type == 'import':
            # Import: Nơi hạ công = place of delivery
            delivery_port = plan_line.goods_delivery_location_id.name if plan_line and plan_line.goods_delivery_location_id else "N/A"
        else:
            # Export: Nơi hạ công = same port
            delivery_port = plan.location_id.name if plan and plan.location_id else "N/A"
        
        goods_weight = f"{plan_line.goods_weight} kg" if plan_line and plan_line.goods_weight else "N/A"
        
        # 2. Đóng hàng/ Hạ Hàng
        loading_time = plan.date.strftime("%d/%m/%Y") if plan and plan.date else "N/A"
        
        # Địa điểm đóng hàng (Loading Address): Different logic for import vs export
        if plan and plan.plan_type == 'import':
            # Import: Địa điểm đóng hàng = address của to location (trong route)
            loading_location = plan_line.route_id.to_location_id.address if plan_line and plan_line.route_id and plan_line.route_id.to_location_id and plan_line.route_id.to_location_id.address else "N/A"
        else:
            # Export: Địa điểm đóng hàng = place of pickup address
            loading_location = plan_line.goods_pickup_location_id.address if plan_line and plan_line.goods_pickup_location_id and plan_line.goods_pickup_location_id.address else "N/A"
        
        contact_number = "N/A"  # No contact_number field in plan model
        
        # Build complete message
        message = f"""1. Thông tin đóng trả hàng:

Số booking/số bill: {booking_bill}
Loại container: {container_info} - hãng tầu ({shipping_line})
Nơi lấy Cont: {pickup_port}
Nơi hạ cont: {delivery_port}
Trọng lượng hàng: {goods_weight}

2. Đóng hàng/ Hạ Hàng

Thời gian đóng hàng: {loading_time}
Địa điểm đóng hàng: {loading_location}
Số liên hệ: {contact_number}"""

        notes= self.note
        message += f"""
        
3. Các Yêu Cầu khác: """

        if notes and notes.strip():
            message += f"""
        
Notes: {notes.strip()}"""
        
        return message

    def action_send_message_bulk(self):
        """Send message via API for multiple selected trips"""
        if not self:
            raise UserError("No trips selected to send messages to.")
        
        # Build message content for the first trip (as preview)
        first_trip = self[0]
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
                'record_id': first_trip.id,  # Use first trip as representative
                'record_model': 'trucking_planning.trip.bulk',  # Special model for bulk
                'message_content': message_content,
                'driver_phone': driver_phone, # Use first trip phone
                'bulk_trip_ids': self.ids,  # Pass all trip IDs
            }
        }

    def action_export_trip_docx(self):
        """Export trip data to DOCX format matching the transport document"""
        return self.env['document.service'].generate_trip_docx(self)

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
            if trip.status in ['cancelled', 'done']:
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
            'res_model': 'trucking_planning.vehicle.driver.history',
            'view_mode': 'list,form',
            'target': 'new',
            'context': {
                'trip_id': self.id,
            },
            "domain": [("end_date", "=", False)],
        }
    
    def _cancel_inactive_trip(self):
        planning_service(self.env).update_trip_statuses('cancelled')
    
    def _close_done_trip(self):
        planning_service(self.env).update_trip_statuses('done')
    
    @api.model
    def recompute_eta_near_status(self):
        """Recompute is_eta_near field for all trips when system parameter changes"""
        trips = self.search([])
        trips._compute_is_eta_near()
        return True

    