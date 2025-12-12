from odoo import models, fields
from odoo.exceptions import UserError
import base64
import io
from datetime import datetime

class DocumentServiceTrucking(models.AbstractModel):
    _name = 'hp.document.service.trucking'
    _inherit = 'hp.document.service'
    _description = 'Document Service For Trucking Planning'

    # Excel plan line
    def generate_excel(self, plan_lines, filename_prefix="plan_lines"):
        """Tạo hàm export excel for plan lines"""
        workbook, output = self._get_excel_workbook()
        worksheet = workbook.add_worksheet('Jobs')
        formats = self._define_excel_formats(workbook)
        self._write_company_info_excel(worksheet, row_start=0, col_start=2)
        headers = self._get_plan_line_headers()
        self._write_excel_header(worksheet, headers, formats, row=8)
        self._write_plan_line_data(worksheet, plan_lines, formats)
        last_data_row = 9 + len(plan_lines) - 1 if plan_lines else 9
        self._write_signature_section_excel(worksheet, workbook, last_data_row)
        for col in range(len(headers)):
            worksheet.set_column(col, col, 15)

        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return self._finalize_excel(workbook, output, filename)

    def _get_plan_line_headers(self):
        # header cho plan line excel
        return [
            'STT', 'Ngày tiếp nhận *', 'Ngày xe chạy *', 'Cut off', 'Mã đối tượng *',
            'Tên đối tượng', 'Tuyến đường *', 'Địa điểm giao', 'Liên hệ', 'Số Job',
            'Số Book/Bill', 'Số Cont *', 'Số Seal', 'Loại NX *', 'Loại Cont',
            'Kích thước cont *', 'Tên hàng hóa dịch vụ', 'Khối lượng', 'Quay đầu', 'Hàng về',
            'Tài xế *', 'Số xe *', 'Số Mooc', 'Xe ngoài', 'Mã chủ PT', 'Phí cầu đường',
            'Phí đi đường', 'Chi phí khác', 'Cự ly', 'Dầu tồn trước', 'Được lĩnh',
            'Tổng cộng dầu', 'Điểm xếp hàng/ Bãi nâng', 'Chi phí nâng', 'Điểm hạ hàng/ bãi hạ',
            'Chi phí hạ', 'Ghi chú', 'Số HĐ', 'Số tờ khai', 'Mã bảng giá'
        ]

    def _write_plan_line_data(self, worksheet, plan_lines, formats):
        """Viết data rows cho plan lines"""
        for row, plan_line in enumerate(plan_lines, start=9):
            trip = plan_line.trip_ids[0] if plan_line.trip_ids else None

            row_data = [
                '',  # STT (sequence - disabled)
                plan_line.date.strftime('%d/%m/%Y %H:%M') if plan_line.plan_id and plan_line.date else '',  # Ngày tiếp nhận
                plan_line.date.strftime('%d/%m/%Y %H:%M') if plan_line.plan_id and plan_line.date else '',  # Ngày xe chạy
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

            self._write_excel_data_row(worksheet, row_data, formats, row, date_columns=[1, 2, 3])

    # docx export for trip
    def generate_docx(self, trip, filename_prefix="trip"):
        """Generate DOCX for trip transport document"""
        if not trip.driver_id:
            raise UserError("No driver id specified")
        if not trip.plan_line_id.date:
            raise UserError("Please fill in the Load / Return Date in the related Plan before exporting the DOCX file.")

        doc = self._get_docx_document()
        # Build document sections
        self._add_docx_company_header(doc, {'style': 'trucking', 'show_logo': False})
        self._add_docx_body(doc, trip)
        # Use base method for footer with trucking config
        signature_config = {
            'signatures': [
                {'title': 'NHÂN VIÊN LÀM LỆNH'},
                {'title': 'LÁI XE NHẬN LỆNH'},
                {'title': 'T/L GIÁM ĐỐC CÔNG TY'}
            ]
        }
        self._add_docx_signature_section(doc, signature_config)

        # Create attachment with ASCII-only filename to avoid encoding issues
        import re
        driver_name = trip.driver_id.name or "TaiXe"
        safe_name = re.sub(r'[^\w\s-]', '', driver_name).strip()
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        trip_date = trip.plan_line_id.date or fields.Datetime.now()
        filename = f"GiayVanTai_{safe_name}_{trip_date.strftime('%d_%m_%Y')}.docx"

        return self._finalize_docx(doc, filename)

    def _add_docx_body(self, doc, trip):
        """Add body content to trip document"""
        self._add_main_info_table(doc, trip)
        self._add_main_content_table(doc, trip)

    def _add_main_info_table(self, doc, trip):
        """Add main info table with driver info and document title"""
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        # Create table with 3 columns for title, info, and driver info
        info_table = doc.add_table(rows=2, cols=3)
        info_table.style = 'Table Grid'
        info_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        self._remove_table_borders(info_table)

        # Merge first column across both rows for driver info
        info_table.cell(0, 0).merge(info_table.cell(1, 0))
        driver_cell = info_table.cell(0, 0)
        self._clear_cell_paragraphs(driver_cell)

        # Add empty paragraphs to push content to bottom
        for i in range(4):
            driver_cell.add_paragraph()

        # Add driver info at the bottom
        driver_para = driver_cell.add_paragraph()
        title_run = driver_para.add_run("2. Thông tin về người lái xe")
        title_run.bold = True
        driver_para.add_run("\nTên tài xế: ")
        bold_run = driver_para.add_run(f"{trip.driver_id.name if trip.driver_id else 'N/A'}")
        bold_run.bold = True
        driver_para.add_run("\nSố điện thoại liên hệ: ")
        bold_run = driver_para.add_run(f"{trip.driver_id.phone if trip.driver_id and trip.driver_id.phone else 'N/A'}")
        bold_run.bold = True

        # Merge 2nd and 3rd columns for the first row (Title)
        info_table.cell(0, 1).merge(info_table.cell(0, 2))
        title_cell = info_table.cell(0, 1)
        self._clear_cell_paragraphs(title_cell)

        title_para = title_cell.add_paragraph()
        title_run = title_para.add_run("GIẤY VẬN TẢI")
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run.bold = True
        title_run.font.size = Pt(14)

        subtitle_para = title_cell.add_paragraph()
        subtitle_run = subtitle_para.add_run(
            "(Ban hành kèm theo Thông tư số: 63/2014/TT-BGTVT ngày 07 tháng 11 năm 2014 của Bộ trưởng Bộ giao thông vận tải)")
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Vehicle and document info
        self._add_vehicle_and_doc_info(info_table, trip)

    def _add_vehicle_and_doc_info(self, info_table, trip):
        """Add vehicle number and document info"""
        vehicle_cell = info_table.cell(1, 1)
        self._clear_cell_paragraphs(vehicle_cell)

        vehicle_cell.add_paragraph()
        vehicle_para = vehicle_cell.add_paragraph()
        vehicle_para.add_run("Số Xe: ")
        bold_run = vehicle_para.add_run(f"{trip.truck_id.name if trip.truck_id and trip.truck_id.name else ' '}")
        bold_run.bold = True
        vehicle_para.add_run("    ")
        vehicle_para.add_run("\nSố Rơ mooc: ")

        # Get trailer name
        trailer_name = ' '
        if trip.trailer_id:
            trailer_name = trip.trailer_id.name
        bold_run = vehicle_para.add_run(f"{trailer_name}")
        bold_run.bold = True

        # Document info cell
        doc_info_cell = info_table.cell(1, 2)
        self._clear_cell_paragraphs(doc_info_cell)

        doc_info_cell.add_paragraph()
        doc_para = doc_info_cell.add_paragraph()
        doc_para.add_run("Số: ")
        bold_run = doc_para.add_run(f"{trip.id}")
        bold_run.bold = True
        doc_para.add_run("\nNgày: ")
        trip_date = trip.plan_line_id.date if trip.plan_line_id and trip.plan_line_id.date else fields.Datetime.now()
        bold_run = doc_para.add_run(f"{trip_date.strftime('%d/%m/%Y')}")
        bold_run.bold = True

    def _add_main_content_table(self, doc, trip):
        """Add main content table with outbound, inbound, and permit sections"""
        from docx.shared import Inches, Pt

        main_table = doc.add_table(rows=2, cols=3)
        main_table.style = 'Table Grid'

        # Header row
        hdr_cells = main_table.rows[0].cells
        # Clear all paragraphs first
        for cell in hdr_cells:
            self._clear_cell_paragraphs(cell)

        hdr_para1 = hdr_cells[0].add_paragraph()
        hdr_para1.add_run("Hàng Đi").bold = True

        hdr_para2 = hdr_cells[1].add_paragraph()
        hdr_para2.add_run("Hàng Về").bold = True

        hdr_para3 = hdr_cells[2].add_paragraph()
        hdr_para3.add_run("Cấp Phép").bold = True

        detail_cells = main_table.rows[1].cells

        # Generate outbound content (Hàng Đi) - with data
        self._generate_trip_section(doc, trip, detail_cells[0], is_outbound=True)

        # Generate inbound content (Hàng Về) - template only
        self._generate_trip_section(doc, trip, detail_cells[1], is_outbound=False)

        # Generate permit section (Cấp Phép)
        self._generate_permit_section(doc, trip, detail_cells[2])

    def _generate_trip_section(self, doc, trip, cell, is_outbound=True):
        """Generate trip section content"""
        self._clear_cell_paragraphs(cell)
        self._add_cell_top_padding(cell)

        show_data = is_outbound
        self._add_booking_info(cell, trip, show_data=show_data)
        self._add_client_info(cell, trip, show_data=show_data)
        self._add_contract_info(cell, trip, show_data=show_data)
        self._add_trip_info(cell, trip, show_data=show_data)
        self._add_goods_info(cell, trip, show_data=show_data)
        self._add_notes(cell, trip, show_data=show_data)

    def _add_booking_info(self, cell, trip, show_data=True):
        """Add booking information section"""
        para = cell.add_paragraph()
        if show_data:
            booking_no = trip.plan_line_id.plan_id.booking_bill_no if trip.plan_line_id and trip.plan_line_id.plan_id else 'N/A'
            title_run = para.add_run(f"Số booking HPL: {booking_no}")
        else:
            title_run = para.add_run("Số booking HPL: ")
        title_run.bold = True
        title_run.underline = True

    def _add_client_info(self, cell, trip, show_data=True):
        """Add client information section"""
        para = cell.add_paragraph()
        title_run = para.add_run("3. Thông tin về người thuê vận tải")
        title_run.bold = True

        content_para = cell.add_paragraph()
        content_para.add_run("Tên người thuê vận chuyển: ")
        if show_data:
            client_name = trip.plan_line_id.client_id.name if trip.plan_line_id and trip.plan_line_id.client_id else 'N/A'
            bold_run = content_para.add_run(f"{client_name}")
            bold_run.bold = True
            content_para.add_run("\nĐịa chỉ: ")
            client_address = getattr(trip.plan_line_id.client_id, 'address',
                                     '') if trip.plan_line_id and trip.plan_line_id.client_id else ''
            bold_run = content_para.add_run(f"{client_address}")
            bold_run.bold = True
        else:
            content_para.add_run("\nĐịa chỉ:")

    def _add_contract_info(self, cell, trip, show_data=True):
        """Add contract information section"""
        para = cell.add_paragraph()
        title_run = para.add_run("4. Thông tin về hợp đồng vận tải")
        title_run.bold = True

        content_para = cell.add_paragraph()
        content_para.add_run("Số hợp đồng: ")
        if show_data:
            route_info = trip.get_route_info() if hasattr(trip, 'get_route_info') else {}

            bold_run = content_para.add_run("")
            bold_run.bold = True
            content_para.add_run("\nSố bill/booking: ")
            bold_run = content_para.add_run(f"{route_info.get('booking_bill', 'N/A')}")
            bold_run.bold = True
            content_para.add_run("\nSố cont: ")
            bold_run = content_para.add_run(f"{trip.container_number or ' '}")
            bold_run.bold = True
            content_para.add_run("\nSố seal: ")
            bold_run = content_para.add_run(f"{trip.seal_number or ' '}")
            bold_run.bold = True
            content_para.add_run("\nLoại cont: ")
            bold_run = content_para.add_run(f"{route_info.get('container_info', 'N/A')}")
            bold_run.bold = True
            content_para.add_run("\nKích thước: ")
            bold_run = content_para.add_run(f"{trip.container_size or '40'}")
            bold_run.bold = True
        else:
            content_para.add_run("\nSố bill/booking:")
            content_para.add_run("\nSố cont:")
            content_para.add_run("\nSố seal:")
            content_para.add_run("\nLoại cont:")
            content_para.add_run("\nKích thước:")

    def _add_trip_info(self, cell, trip, show_data=True):
        """Add trip information section"""
        para = cell.add_paragraph()
        title_run = para.add_run("5. Thông tin về chuyến đi")
        title_run.bold = True

        content_para = cell.add_paragraph()
        content_para.add_run("Tuyến vận chuyển: ")
        if show_data:
            route_name = trip.plan_line_id.route_id.name if trip.plan_line_id and trip.plan_line_id.route_id else ' '
            bold_run = content_para.add_run(f"{route_name}")
            bold_run.bold = True

            content_para.add_run("\nĐiểm xếp hàng: ")
            route_info = trip.get_route_info() if hasattr(trip, 'get_route_info') else {}
            loading_location = route_info.get('loading_location', ' ')
            bold_run = content_para.add_run(f"{loading_location}")
            bold_run.bold = True

            content_para.add_run("\nĐiểm giao hàng: ")
            pickup_port = route_info.get('pickup_port', 'N/A')
            bold_run = content_para.add_run(f"{pickup_port}")
            bold_run.bold = True

            content_para.add_run("\nNơi trả hàng: ")
            delivery_port = route_info.get('delivery_port', 'N/A')
            bold_run = content_para.add_run(f"{delivery_port}")
            bold_run.bold = True

            content_para.add_run("\nThời gian vận chuyển dự kiến:")
            content_para.add_run("\nBắt đầu từ : ")
            etd_str = trip.plan_line_id.estimate_time_departure.strftime(
                '%d/%m/%Y %H:%M') if trip.plan_line_id and trip.plan_line_id.estimate_time_departure else ' '
            bold_run = content_para.add_run(f"{etd_str}")
            bold_run.bold = True

            content_para.add_run("\nđến: ")
            eta_str = trip.plan_line_id.estimate_time_arrival.strftime(
                '%d/%m/%Y %H:%M') if trip.plan_line_id and trip.plan_line_id.estimate_time_arrival else ' '
            bold_run = content_para.add_run(f"{eta_str}")
            bold_run.bold = True

            content_para.add_run("\nTổng số km dự kiến: ")
            distance = trip.plan_line_id.route_id.distance_km if trip.plan_line_id and trip.plan_line_id.route_id else ''
            bold_run = content_para.add_run(f"{distance}")
            bold_run.bold = True

            content_para.add_run("\nLiên hệ: ")
            bold_run = content_para.add_run(" ")
            bold_run.bold = True
        else:
            content_para.add_run("\nĐiểm xếp hàng:")
            content_para.add_run("\nĐiểm giao hàng:")
            content_para.add_run("\nNơi trả hàng:")
            content_para.add_run("\nThời gian vận chuyển dự kiến:")
            content_para.add_run("\nBắt đầu từ: ")
            content_para.add_run("\nđến: ")
            content_para.add_run("\nTổng số km dự kiến: ")
            content_para.add_run("\nLiên hệ:")

    def _add_goods_info(self, cell, trip, show_data=True):
        """Add goods information section"""
        para = cell.add_paragraph()
        title_run = para.add_run("6. Thông tin về hàng hóa")
        title_run.bold = True

        content_para = cell.add_paragraph()
        content_para.add_run("Tên hàng hóa: ")
        if show_data:
            route_info = trip.get_route_info() if hasattr(trip, 'get_route_info') else {}

            bold_run = content_para.add_run(f"{trip.goods_name or ' '}")
            bold_run.bold = True

            content_para.add_run("\nKhối lượng hàng hóa (tấn): ")
            bold_run = content_para.add_run(f"{route_info.get('goods_weight', ' ')}")
            bold_run.bold = True

            content_para.add_run("\nCắt máng (Cut off): ")
            cut_off_str = trip.goods_cut_off.strftime('%d/%m/%Y %H:%M') if trip.goods_cut_off else ' '
            bold_run = content_para.add_run(f"{cut_off_str}")
            bold_run.bold = True
        else:
            content_para.add_run("\nKhối lượng hàng hóa (tấn): ")
            content_para.add_run("\nCắt máng(Cut off):")

    def _add_notes(self, cell, trip, show_data=True):
        """Add notes section"""
        para = cell.add_paragraph()
        title_run = para.add_run("7. Ghi chú: ")
        title_run.bold = True

        if show_data:
            route_info = trip.get_route_info() if hasattr(trip, 'get_route_info') else {}
            content_para = cell.add_paragraph()
            bold_run = content_para.add_run(f"{route_info.get('notes', ' ')}")
            bold_run.bold = True

    def _generate_permit_section(self, doc, trip, cell):
        """Generate permit section with fuel and cost information"""
        self._clear_cell_paragraphs(cell)
        self._add_cell_top_padding(cell)

        # Fuel info
        para1_permit = cell.add_paragraph()
        title_run = para1_permit.add_run("Nhiên Liệu - (LÍT DIZEL)")
        title_run.bold = True

        cell.add_paragraph()
        para1_permit_content = cell.add_paragraph()
        para1_permit_content.add_run("Tồn trước (lít): ")
        bold_run = para1_permit_content.add_run(" ")
        bold_run.bold = True
        para1_permit_content.add_run("\nĐược lĩnh (lít): ")
        bold_run = para1_permit_content.add_run(f"{trip.fuel_liters or ''}")
        bold_run.bold = True
        para1_permit_content.add_run("\nTổng cộng (lít): ")
        bold_run = para1_permit_content.add_run(" ")
        bold_run.bold = True

        # Add cost info
        cell.add_paragraph()
        cell.add_paragraph()
        para2_permit = cell.add_paragraph()
        title_run = para2_permit.add_run("TIỀN CHI PHÍ - (ĐỒNG)")
        title_run.bold = True

        para2_permit_content = cell.add_paragraph()
        road_fee = getattr(trip.plan_line_id.route_id, 'road_fee',
                           '') if trip.plan_line_id and trip.plan_line_id.route_id else ''
        if road_fee == 0:
            road_fee = ''

        para2_permit_content.add_run("Vé cầu đường: ")
        bold_run = para2_permit_content.add_run(f"{road_fee}")
        bold_run.bold = True

        para2_permit_content.add_run("\nChi phí khác: ")
        bold_run = para2_permit_content.add_run(f"{trip.extra_charge or ''}")
        bold_run.bold = True

        para2_permit_content.add_run("\nĐi đường: ")
        bold_run = para2_permit_content.add_run("")
        bold_run.bold = True

        para2_permit_content.add_run("\nTổng Cộng: ")
        bold_run = para2_permit_content.add_run(f"{trip.total_cost or ''}")
        bold_run.bold = True

        for _ in range(4):
            cell.add_paragraph()

        para3_permit = cell.add_paragraph()
        para3_permit.add_run("Nâng hàng/vỏ: ")
        bold_run = para3_permit.add_run(" ")
        bold_run.bold = True
        para3_permit.add_run("\nHạ vỏ/hàng: ")
        bold_run = para3_permit.add_run(" ")
        bold_run.bold = True
        para3_permit.add_run("\nTổng cộng: ")
        bold_run = para3_permit.add_run(" ")
        bold_run.bold = True
        para3_permit.add_run("\nTổng Tiền: ")
        bold_run = para3_permit.add_run(f"{trip.total_cost or ''}")
        bold_run.bold = True