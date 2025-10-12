from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError
import base64
import math
import logging
from datetime import datetime, timedelta
from ..services.planning_service import planning_service
from ..services.res_partner_service import ResPartnerService
from ...hp_components.services.partner_service import PartnerService

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
        related='plan_line_id.plan_id.date',
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
        partner_service = PartnerService(self.env)
        return [('partner_main_type_id', '=',partner_service.get_partner_main_type_driver().id)]

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

    def toggle_active(self):
        for trip in self:
            if trip.status not in ['draft', 'cancelled']:
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
                'status': 'draft',
            }
            new_trip = self.create(new_vals)

            return new_trip

    def get_conflicting_trip(self, vehicle_assignment_log):
        if not self or not self.plan_estimate_time_departure or not self.plan_estimate_time_arrival:
            return self.browse()

        domain = [
            ("id", "!=", self.id),
            ("active", "=", True),
            ("vehicle_assignment_log_id", "=", vehicle_assignment_log.id),
            ("plan_estimate_time_departure", "<=", self.plan_estimate_time_arrival),
            ("plan_estimate_time_arrival", ">=", self.plan_estimate_time_departure),
            ("vehicle_assignment_log_id.date_end", "=", False),
        ]

        return self.search(domain)

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
                        ('status', 'not in', ['cancelled']),
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
        """Common method to get route and location information for a trip"""
        plan_line = self.plan_line_id
        plan = plan_line.plan_id if plan_line else None

        result = {
            'booking_bill': 'N/A',
            'container_info': 'N/A',
            'shipping_line': 'N/A',
            'pickup_port': 'N/A',
            'delivery_port': 'N/A',
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
        if plan and plan.location_id:
            result['pickup_port'] = plan.location_id.name or 'N/A'

        # Nơi hạ công (Delivery Port): Different logic for import vs export
        if plan and plan.plan_type == 'import':
            # Import: Nơi hạ công = place of delivery
            location = plan_line.goods_delivery_location_id if plan_line else None
            if location:
                address = location.address or ''
                delivery_port = f"{location.name} ({address})" if address else location.name
            result['delivery_port'] = delivery_port
        else:
            # Export: Nơi hạ công = same port
            result['delivery_port'] = plan.location_id.name if plan and plan.location_id else 'N/A'

        if plan_line and plan_line.goods_weight:
            result['goods_weight'] = f"{plan_line.goods_weight} Tấn"

        # 2. Đóng hàng/ Hạ Hàng
        if plan and plan.date:
            user_tz = self.env.user.tz or 'Asia/Ho_Chi_Minh'
            localized_date = fields.Datetime.context_timestamp(self, plan.date)
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

        message = f"""1. Thông tin đóng trả hàng:

        Số booking/số bill: {route_info['booking_bill']}
        Loại container: {route_info['container_info']} - hãng tầu ({route_info['shipping_line']})
        Nơi lấy Cont: {route_info['pickup_port']}
        Nơi hạ cont: {route_info['delivery_port']}
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
        return self.env['hp.document.service'].generate_trip_docx(self)

    def action_export_trip_docx_bulk(self):
        """Export selected trips to DOCX and return a ZIP download"""
        if not self:
            raise UserError("No trips selected to export.")

        import io
        import zipfile
        import re

        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for trip in self:
                # Reuse document service to build the Document
                doc = self.env['hp.document.service']._generate_trip_docx(trip)

                # Save document to bytes
                doc_io = io.BytesIO()
                doc.save(doc_io)
                doc_io.seek(0)

                # Build safe filename, mirroring single export
                driver_name = trip.driver_id.name if trip.driver_id else 'N_A'
                safe_driver_name = re.sub(r'[^\w\s-]', '', driver_name).strip()
                safe_driver_name = re.sub(r'[-\s]+', '_', safe_driver_name)
                trip_date = trip.plan_line_id.plan_id.date if trip.plan_line_id and trip.plan_line_id.plan_id else fields.Datetime.now()
                if isinstance(trip_date, datetime):
                    filename = f"GiayVanTai_{safe_driver_name}_{trip_date.strftime('%d_%m_%Y')}.docx"
                else:
                    filename = f"GiayVanTai_{safe_driver_name}_{trip_date.date().strftime('%d_%m_%Y')}.docx"

                # Write into ZIP
                zipf.writestr(filename, doc_io.getvalue())

        zip_io.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'GiayVanTai_All_Selected.zip',
            'type': 'binary',
            'datas': base64.b64encode(zip_io.getvalue()),
            'mimetype': 'application/zip',
            'res_model': self._name,
            'res_id': self[0].id,
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
            'res_model': 'fleet.vehicle.assignation.log',
            'view_mode': 'list,form',
            'target': 'new',
            'context': {
                'trip_id': self.id,
            },
            "domain": [("date_end", "=", False)],
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
                        ('status', 'not in', ['cancelled', 'done'])
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

    