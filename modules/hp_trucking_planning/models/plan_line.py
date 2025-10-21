from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
import base64
import math
import io
from datetime import datetime
from ..services.zalo_service import ZaloService
from ..services.res_partner_service import ResPartnerService

import logging
_logger = logging.getLogger(__name__)

class PlanLine(models.Model):
    _name = 'trucking_planning.plan.line'
    _description = 'Job'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'code'

    plan_id = fields.Many2one(
        comodel_name='trucking_planning.plan',
        string='Plan',
        required=True,
        readonly=True,
    )
    code = fields.Char(
        string='Job Number',
        tracking=True,
        required=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner.client',
        required=True,
        domain=[('partner_main_type_id.code','=', ResPartnerService.PARTNER_TYPE_CLIENT)]
    )
    tax_number = fields.Char(
        string='Tax Number',
        related='client_id.vat',
        store=False,
    )
    status = fields.Selection([
        ('hpl_reject', 'HPL Reject'),
        ('client_cancel', 'Client Cancel'),
        ('checking', 'Checking'),
        ('transfer', 'Transfer'),
        ('rented', 'Rented')
    ],
        string='Status',
        required=True,
        tracking=True,
    )
    plan_type = fields.Selection([],
                                 related='plan_id.plan_type',
                                 store=False,
                                 )
    route_id = fields.Many2one(
        comodel_name='trucking_planning.route', required=True
    )
    actual_source_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string='From Location',
        store=True,
        readonly=True,
        tracking=True,
    )
    actual_destination_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string='To Location',
        store=True,
        readonly=True,
        tracking=True,
    )
    note = fields.Text(string="Note")

    # goods info
    goods_name = fields.Char(
        string="Goods Name",
    )
    goods_weight = fields.Float(
        string="Goods Weight",
    )
    trip_ids = fields.One2many(
        comodel_name='trucking_planning.trip',
        string='Trip',
        inverse_name='plan_line_id',
    )

    truck_count = fields.Integer(
        string="Trucks",
        compute='_compute_truck_count',
        store=True,
        help="Number of trucks assigned to this customer"
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
        required=True,
        tracking=True,
        domain=[('type', '=', 'goods_pickup_delivery')],
        help="Location where goods will be picked up (Export) or delivered (Import)"
    )
    goods_delivery_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        string="Goods Delivery Location",
        required=True,
        tracking=True,
        domain=[('type', '=', 'port')],
        help="Location where goods will be delivered (Export) or picked up (Import)"
    )

    combined_vehicles = fields.Integer(
        string="Combined Vehicles",
        computed='_compute_vehicle_count',
        store=False,
        help="Number of combined vehicles"
    )
    external_vehicles = fields.Integer(
        string="External Vehicles",
        compute='_compute_vehicle_counts',
        store=False,
        help="Number of external vehicles in this job"
    )

    assigned_trucks = fields.Integer(
        string="Assigned Trucks",
        compute='_compute_vehicle_counts',
        store=False,
        help="Number of trips with assigned trucks"
    )

    unassigned_trucks = fields.Integer(
        string="Unassigned Trucks",
        compute='_compute_vehicle_counts',
        store=False,
        help="Number of trips without assigned trucks"
    )

    container_summary = fields.Char(
        string="Container Summary",
        compute='_compute_container_summary',
        store=False
    )

    container_number_summary = fields.Char(
        string="Container Numbers (Số Cont)",
        compute='_compute_container_number_summary',
        store=False,
        help="Comma-separated container numbers from trips"
    )

    weight_class_summary = fields.Char(
        string="Weight Class",
        compute='_compute_weight_class_summary',
        store=False,
        help="Comma-separated weight classes from trips"
    )

    trip_status_summary = fields.Char(
        string="Trip Status",
        compute='_compute_trip_status_summary',
        store=False,
        help="Summary of trip statuses: Incomplete (Draft, On Route, Stopped) / Done"
    )

    @api.depends('trip_ids.status', 'trip_ids.active')
    def _compute_trip_status_summary(self):
        for record in self:
            active_trips = record.trip_ids.filtered(lambda t: t.active)
            # Đếm số chuyến chưa hoàn thành (draft, on_route, stopped)
            incomplete_trips = active_trips.filtered(
                lambda t: t.status in ['draft', 'on_route', 'stopped']
            )
            # Đếm số chuyến đã hoàn thành (done)
            done_trips = active_trips.filtered(
                lambda t: t.status == 'done'
            )
            record.trip_status_summary = f"{len(incomplete_trips)} Incomplete / {len(done_trips)} Done"

    @api.depends('trip_ids.container_number')
    def _compute_container_number_summary(self):
        for record in self:
            trips = record.trip_ids.filtered(lambda t: t.active and t.container_number)
            numbers = ', '.join(sorted(set(trips.mapped('container_number')))) if trips else 'N/A'
            record.container_number_summary = numbers

    @api.depends('trip_ids.weight_class')
    def _compute_weight_class_summary(self):
        for record in self:
            trips = record.trip_ids.filtered(lambda t: t.active and t.weight_class)
            classes = ', '.join(sorted(set(trips.mapped('weight_class')))) if trips else 'N/A'
            record.weight_class_summary = classes

    @api.depends('trip_ids.container_type', 'trip_ids.container_size')
    def _compute_container_summary(self):
        for record in self:
            trips = record.trip_ids.filtered(lambda t: t.active)
            types = ', '.join(trips.mapped('container_type')) if trips.mapped('container_type') else 'N/A'
            sizes = ', '.join(trips.mapped('container_size')) if trips.mapped('container_size') else 'N/A'
            record.container_summary = f"{types} ({sizes})"

    @api.depends('trip_ids.is_combined_vehicle', 'trip_ids.is_external_vehicle', 'trip_ids.truck_id', 'trip_ids.active')
    def _compute_vehicle_counts(self):
        for record in self:
            trips = record.trip_ids.filtered(lambda t: t.active)
            record.combined_vehicles = len(trips.filtered(lambda t: t.is_combined_vehicle))
            record.external_vehicles = len(trips.filtered(lambda t: t.is_external_vehicle))
            record.assigned_trucks = len(trips.filtered(lambda t: t.truck_id))
            record.unassigned_trucks = len(trips) - record.assigned_trucks

    @api.constrains('code')
    def _check_unique_job_number(self):
        for record in self:
            if record.code:
                existing_job = self.env['trucking_planning.plan.line'].search([
                    ('code', '=', record.code),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing_job:
                    booking_info = existing_job.plan_id.booking_bill_no if existing_job.plan_id else ''
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    view_url = f"{base_url}/web#id={existing_job.id}&model=trucking_planning.plan.line&view_type=form"
                    error_message = f"""Job Number '{record.code}' already exists!

                        Job Details:
                        - Job Number: {existing_job.code}
                        - Booking/Bill No: {booking_info}
                        - Plan: {existing_job.plan_id.name if existing_job.plan_id else ''}
                        - Client: {existing_job.client_id.name if existing_job.client_id else ''}
                        - Route: {existing_job.route_id.name if existing_job.route_id else ''}
                        - Estimated Time of Departure: {existing_job.estimate_time_departure.strftime('%d/%m/%Y %H:%M') if existing_job.estimate_time_departure else ''}
                        - Estimated Time of Arrival: {existing_job.estimate_time_arrival.strftime('%d/%m/%Y %H:%M') if existing_job.estimate_time_arrival else ''}
                        - Status: {existing_job.status}

                        View existing job: {view_url}

                        Choose a different Job Number."""

                    raise UserError(error_message)

    @api.onchange('plan_type')
    def _onchange_plan_type(self):
        for record in self:
            if record.plan_type == 'export':
                # Export: chỉ cần pickup location, delivery sẽ là port
                record.goods_pickup_location_id = False
                record.goods_delivery_location_id = record.plan_id.location_id
            else:
                # Import: chỉ cần delivery location, pickup sẽ là port
                record.goods_pickup_location_id = record.plan_id.location_id
                record.goods_delivery_location_id = False

    @api.constrains('estimate_time_departure', 'estimate_time_arrival', 'plan_type')
    def _check_estimate_time(self):
        for record in self:
            if record.estimate_time_departure and record.estimate_time_arrival:
                if record.plan_type == 'export':
                    if record.estimate_time_arrival >= record.estimate_time_departure:
                        raise ValidationError(
                            "For Export jobs, Estimated Time of Arrival must be earlier than Estimated Time of Departure.")
                else:
                    if record.estimate_time_arrival <= record.estimate_time_departure:
                        raise ValidationError(
                            "For Import jobs, Estimate Time of Arrival must be later than Estimate Time of Departure.")

    @api.depends('estimate_time_departure', 'estimate_time_arrival')
    def _compute_estimate_time_duration(self):
        for rec in self:
            if rec.estimate_time_departure and rec.estimate_time_arrival:
                delta = rec.estimate_time_arrival - rec.estimate_time_departure
                rec.estimate_time_duration = delta.total_seconds() / 3600.0
            else:
                rec.estimate_time_duration = 0.0
    # --- MISSING FIELDS IN EXCEL FILE ---
    # sequence = fields.Char(string="STT")
    # delivery_location = fields.Text(string="Địa điểm giao")
    # contact_info = fields.Char(string="Liên hệ", related='client_id.phone', readonly=True)
    # operation_type = fields.Selection([
    #     ('import', 'Nhập'),
    #     ('export', 'Xuất')
    # ], string="Loại NX", default='export', related='plan_id.plan_type', readonly=True)
    # turnaround = fields.Boolean(string="Quay đầu", default=False)
    # goods_return = fields.Boolean(string="Hàng về", default=False)
    # external_vehicle = fields.Boolean(string="Xe ngoài", default=False)
    # owner_code = fields.Char(string="Mã chủ PT", default='NONE')
    # road_fee = fields.Float(string="Phí cầu đường", related='route_id.road_fee', readonly=True)
    # distance = fields.Float(string="Cự ly", related='route_id.distance_km', readonly=True)
    # fuel_before = fields.Float(string="Dầu tồn trước", default=0.0)
    # fuel_received = fields.Float(string="Được lĩnh", default=0.0)
    # fuel_total = fields.Float(string="Tổng cộng dầu", compute='_compute_fuel_total', store=True)
    # loading_location = fields.Char(string="Điểm xếp hàng/ Bãi nâng")
    # loading_cost = fields.Float(string="Chi phí nâng", default=0.0)
    # unloading_location = fields.Char(string="Điểm hạ hàng/ bãi hạ")
    # unloading_cost = fields.Float(string="Chi phí hạ", default=0.0)
    # contract_number = fields.Char(string="Số HĐ")
    # declaration_number = fields.Char(string="Số tờ khai")
    # price_code = fields.Char(string="Mã bảng giá")

    @api.depends('trip_ids.active')
    def _compute_truck_count(self):
        for record in self:
            record.truck_count = len(record.trip_ids.filtered(lambda t: t.active))

    @api.depends('plan_type', 'route_id')
    def _compute_actual_locations(self):
        for rec in self:
            if rec.route_id:
                # So sánh direction của route với plan_type
                if rec.route_id.direction == rec.plan_type:
                    # Giống nhau: giữ nguyên from -> to
                    rec.actual_source_location_id = rec.route_id.from_location_id
                    rec.actual_destination_location_id = rec.route_id.to_location_id
                else:
                    # Khác nhau: đảo ngược to -> from
                    rec.actual_source_location_id = rec.route_id.to_location_id
                    rec.actual_destination_location_id = rec.route_id.from_location_id
            else:
                rec.actual_source_location_id = False
                rec.actual_destination_location_id = False

    def _compute_route_info(self):
        for trip in self:
            freeway_text = '(freeway)' if trip.freeway else ''
            trip.route_info = f"{trip.actual_source_location_id.name} - {trip.actual_destination_location_id.name} {freeway_text}"

    def _compute_container_info(self):
        for trip in self:
            trip.container_info = f"{trip.container_type},{trip.container_size}"

    def _compute_location_info(self):
        for trip in self:
            contact_info = f"({trip.contact_phone})" if trip.contact_phone else ""
            trip.location_info = f"{trip.container_pickup.name},{trip.goods_pickup_delivery.name} {contact_info},{trip.container_delivery.name}"

    def _compute_driver_info(self):
        for trip in self:
            trip.driver_info = f"{trip.driver_id.name},{trip.truck_id.name}"

    @api.onchange('route_id')
    def _on_route_change(self):
        for trip in self:
            trip.plan_type = trip.route_id.direction

    def action_view_trips(self):
        """Action để xem tất cả trips thuộc job"""
        self.ensure_one()
        return {
            'name': f'Trucks - {self.code or self.plan_id.name}',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'list,form',
            'domain': [('plan_line_id', '=', self.id)],
            'context': {
                'default_plan_line_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    def action_add_truck(self):
        """Action để add truck cho customer """
        self.ensure_one()
        return {
            'name': f'Add Truck - {self.code or self.client_id.name}',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_trucking_planning.view_trip_form').id,
            'context': {
                'default_plan_line_id': self.id,
                'default_plan_id': self.plan_id.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_add_draft_trip(self):
        self.ensure_one()
        return {
            'name': f'Add Draft Trips - {self.code or self.client_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'trucking_planning.add_draft_trip.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_plan_line_id': self.id,
                'default_plan_id': self.plan_id.id,
            }
        }

    def _create_draft_trips(self, number_of_trips):
        self.ensure_one()
        if number_of_trips <= 0:
            return

        trucks_created = []
        for i in range(number_of_trips):
            truck_vals = {
                'plan_line_id': self.id,
                'container_type': self.plan_id.container_type,
                'container_size': '40',
                'weight_class': 'mix',
                'status': 'draft',
            }
            trip = self.env['trucking_planning.trip'].create(truck_vals)
            trucks_created.append(trip.id)

        if trucks_created:
            message = f"Created {len(trucks_created)} draft trip(s) for {self.client_id.name}"
            self.message_post(body=message, message_type='notification')


    def action_send_message(self):
        """Send message via API for job - sends to all drivers of trips"""
        if not self.trip_ids:
            raise UserError("No trips found in this job to send messages to.")
        
        # Build message content for the first trip (as preview)
        first_trip = self.trip_ids[0]
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

    def action_export_plan_line_excel(self):
        """Export job data to Excel format"""
        return self.env['hp.document.service'].generate_plan_line_excel(self)

    def action_export_all_plan_lines_excel(self):
        """Export all jobs to Excel format"""
        return self.search([]).action_export_plan_line_excel()

    # @api.depends('fuel_before', 'fuel_received')
    # def _compute_fuel_total(self):
    #     for record in self:
    #         record.fuel_total = record.fuel_before + record.fuel_received
