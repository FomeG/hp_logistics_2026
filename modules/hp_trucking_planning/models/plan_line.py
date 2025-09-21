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
        domain=[('type','=', ResPartnerService.PARTNER_TYPE_CLIENT)]
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


    @api.depends('trip_ids')
    def _compute_truck_count(self):
        """Compute the number of trucks (trips) for this customer"""
        for record in self:
            record.truck_count = len(record.trip_ids)

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
        try:
            import xlsxwriter
        except ImportError:
            raise UserError("xlsxwriter library is required. Please install it using: pip install xlsxwriter")

        # Create workbook and worksheet
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Jobs')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#90EE90',  # Light green background
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })

        date_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'num_format': 'dd/mm/yyyy hh:mm'
        })

        # Company information (C1 to C5)
        company_info = [
            "CHI NHÁNH CÔNG TY CP TIẾP VẬN HP TẠI TP.HẢI PHÒNG",
            "Room 202A, Dau Khi Hotel, 441 Da Nang Street, Hai An, Hai Phong, Vietnam",
            "Tel: + 84 225 3556133 Fax: + 84 225 3556132",
            "Email: cs@hplogistics.com.vn",
            "Website: www.hplogistics.com.vn"
        ]

        for i, info in enumerate(company_info):
            worksheet.write(i, 2, info)  # Column C (index 2)

        # Headers (Row 9)
        headers = [
            'STT', 'Ngày tiếp nhận *', 'Ngày xe chạy *', 'Cut off', 'Mã đối tượng *', 
            'Tên đối tượng', 'Tuyến đường *', 'Địa điểm giao', 'Liên hệ', 'Số Job',
            'Số Book/Bill', 'Số Cont *', 'Số Seal', 'Loại NX *', 'Loại Cont',
            'Kích thước cont *', 'Tên hàng hóa dịch vụ', 'Khối lượng', 'Quay đầu', 'Hàng về',
            'Tài xế *', 'Số xe *', 'Số Mooc', 'Xe ngoài', 'Mã chủ PT', 'Phí cầu đường',
            'Phí đi đường', 'Chi phí khác', 'Cự ly', 'Dầu tồn trước', 'Được lĩnh',
            'Tổng cộng dầu', 'Điểm xếp hàng/ Bãi nâng', 'Chi phí nâng', 'Điểm hạ hàng/ bãi hạ',
            'Chi phí hạ', 'Ghi chú', 'Số HĐ', 'Số tờ khai', 'Mã bảng giá'
        ]

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(8, col, header, header_format)  # Row 9 (index 8)

        # Get jobs data
        plan_lines = self
        
        # Write data rows
        for row, plan_line in enumerate(plan_lines, start=9):  # Start from row 10 (index 9)
            # Get related trip data (first trip for this job)
            trip = plan_line.trip_ids[0] if plan_line.trip_ids else None
            
            # Prepare row data
            row_data = [
                '',  # STT (sequence - disabled)
                plan_line.plan_id.date.strftime('%d/%m/%Y %H:%M') if plan_line.plan_id and plan_line.plan_id.date else '',  # Ngày tiếp nhận
                plan_line.plan_id.date.strftime('%d/%m/%Y %H:%M') if plan_line.plan_id and plan_line.plan_id.date else '',  # Ngày xe chạy
                plan_line.plan_id.goods_cut_off.strftime('%d/%m/%Y %H:%M') if plan_line.plan_id and plan_line.plan_id.goods_cut_off else '',  # Cut off
                plan_line.client_id.code if plan_line.client_id and hasattr(plan_line.client_id, 'code') else '',  # Mã đối tượng
                plan_line.client_id.name if plan_line.client_id else '',  # Tên đối tượng
                plan_line.route_id.name if plan_line.route_id else '',  # Tuyến đường
                '',  # Địa điểm giao (disabled)
                '',  # Liên hệ (disabled)
                plan_line.code or '',  # Số Job
                plan_line.plan_id.booking_bill_no if plan_line.plan_id else '',  # Số Book/Bill
                trip.container_number if trip else '',  # Số Cont
                trip.seal_number if trip else '',  # Số Seal
                ('Xuất' if (plan_line.plan_id and plan_line.plan_id.plan_type == 'export') else 'Nhập') if plan_line.plan_id else '',  # Loại NX
                (trip.container_type if trip and trip.container_type else ''),  # Loại Cont
                (trip.container_size if trip and trip.container_size else ''),  # Kích thước cont
                plan_line.goods_name or '',  # Tên hàng hóa dịch vụ
                str(plan_line.goods_weight) if plan_line.goods_weight else '',  # Khối lượng
                '',  # Quay đầu (disabled)
                '',  # Hàng về (disabled)
                (trip.driver_id.name if trip and trip.driver_id else ''),  # Tài xế
                (trip.truck_id.name if trip and trip.truck_id else ''),  # Số xe
                (trip.trailer_id.name if trip and trip.trailer_id else ''),  # Số Mooc
                'Indeterminate',  # Xe ngoài (no field yet)
                'NONE',  # Mã chủ PT (default)
                '',  # Phí cầu đường (disabled)
                str(getattr(plan_line.route_id, 'road_fee', '') if plan_line.route_id else ''),  # Phí đi đường
                str(getattr(trip, 'extra_charge', '') if trip else ''),  # Chi phí khác
                '0.0',  # Cự ly (disabled)
                '',  # Dầu tồn trước (disabled)
                '',  # Được lĩnh (disabled)
                '',  # Tổng cộng dầu (disabled)
                '',  # Điểm xếp hàng/ Bãi nâng (disabled)
                '',  # Chi phí nâng (disabled)
                '',  # Điểm hạ hàng/ bãi hạ (disabled)
                '',  # Chi phí hạ (disabled)
                plan_line.note or '',  # Ghi chú
                '',  # Số HĐ (disabled)
                '',  # Số tờ khai (disabled)
                ''   # Mã bảng giá (disabled)
            ]

            # Write row data
            for col, value in enumerate(row_data):
                if col in [1, 2, 3]:  # Date columns
                    worksheet.write(row, col, value, date_format)
                else:
                    worksheet.write(row, col, value, cell_format)

        # Set column widths
        for col in range(len(headers)):
            worksheet.set_column(col, col, 15)

        # Determine last data row (0-indexed)
        last_data_row = 9 + len(plan_lines) - 1 if plan_lines else 9

        # Signature and footer sections relative to last table row
        center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        center_bold_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})
        italic_center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'italic': True})
        merged_border = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 0})

        # Column A merged to B at +7, +8, +12
        worksheet.merge_range(last_data_row + 7, 0, last_data_row + 7, 1, 'Người lập phiếu', merged_border)
        worksheet.merge_range(last_data_row + 8, 0, last_data_row + 8, 1, '(Ký, họ tên)', italic_center_format)
        worksheet.merge_range(last_data_row + 12, 0, last_data_row + 12, 1, 'Lê Quý Hùng', center_bold_format)

        # Column T at +7, +8
        col_T = 19
        worksheet.write(last_data_row + 7, col_T, 'Kế toán trưởng', center_bold_format)
        worksheet.write(last_data_row + 8, col_T, '(Ký, họ tên)', italic_center_format)

        # Column AM at +6, +7, +8, +12
        col_AM = 38  # Column AM (zero-based)
        worksheet.write(last_data_row + 6, col_AM, 'Ngày …..  tháng …..  năm 201….', center_format)
        worksheet.write(last_data_row + 7, col_AM, 'Giám đốc', center_bold_format)
        worksheet.write(last_data_row + 8, col_AM, '(Đóng dấu, ký tên)', italic_center_format)
        worksheet.write(last_data_row + 12, col_AM, 'Nguyễn Văn Bân', center_bold_format)

        workbook.close()
        output.seek(0)

        # Create attachment
        filename = f"Plan_Lines_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id if len(self) == 1 else False,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_export_all_plan_lines_excel(self):
        """Export all jobs to Excel format"""
        return self.search([]).action_export_plan_line_excel()

    # @api.depends('fuel_before', 'fuel_received')
    # def _compute_fuel_total(self):
    #     for record in self:
    #         record.fuel_total = record.fuel_before + record.fuel_received
