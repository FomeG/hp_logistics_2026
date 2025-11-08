from odoo import models, api, fields
from odoo.exceptions import UserError
import base64
import io
from datetime import datetime

class HpDocumentService(models.AbstractModel):
    _name = 'hp.document.service'
    _description = 'Document Service Library'

    def generate_trip_docx(self, trip):
        """Generate trip data to DOCX format matching the transport document"""
        try:
            from docx import Document
            from docx.shared import Inches, Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.table import WD_TABLE_ALIGNMENT
        except ImportError:
            raise UserError("python-docx library is required. Please install it using: pip install python-docx")

        if not trip.driver_id:
            raise UserError("No driver id specified")

        if not trip.plan_line_id.date:
            raise UserError("Please fill in the Load / Return Date in the related Plan before exporting the DOCX file.")

        try:
            # Generate the DOCX file
            doc = self._generate_trip_docx(trip)

            # Save document to memory
            doc_io = io.BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)

            # Create attachment with ASCII-only filename to avoid encoding issues
            driver_name = trip.driver_id.name if trip.driver_id else 'N/A'
            # Remove Vietnamese characters and special characters from filename
            import re
            safe_driver_name = re.sub(r'[^\w\s-]', '', driver_name).strip()
            safe_driver_name = re.sub(r'[-\s]+', '_', safe_driver_name)
            trip_date = trip.plan_line_id.date if trip.plan_line_id else fields.Datetime.now()
            if isinstance(trip_date, datetime):
                filename = f"GiayVanTai_{safe_driver_name}_{trip_date.strftime('%d_%m_%Y')}.docx"
            else:
                filename = f"GiayVanTai_{safe_driver_name}_{trip_date.date().strftime('%d_%m_%Y')}.docx"
            
            attachment = trip.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(doc_io.read()),
                'res_model': trip._name,
                'res_id': trip.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            })

            # Return download action
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        except Exception as e:
            # Log the error for debugging
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Error generating DOCX for trip {trip.id}: {str(e)}")
            raise UserError(f"Error generating DOCX file: {str(e)}")

    def generate_plan_line_excel(self, plan_lines):
        """Export plan line data to Excel format"""
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
        plan_lines = plan_lines
        
        # Write data rows
        for row, plan_line in enumerate(plan_lines, start=9):  # Start from row 10 (index 9)
            # Get related trip data (first trip for this job)
            trip = plan_line.trip_ids[0] if plan_line.trip_ids else None
            
            # Prepare row data
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
        attachment = plan_lines.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': plan_lines._name,
            'res_id': plan_lines.id if len(plan_lines) == 1 else False,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _generate_trip_docx(self, trip):
        """Main method to generate the complete DOCX document"""
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        doc = Document()

        # Set margins
        for section in doc.sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)

        # Set default font to Tahoma
        style = doc.styles['Normal']
        style.font.name = 'Tahoma'
        style.font.size = Pt(9.5)

        # Generate document sections
        self._generate_header_section(doc)
        self._generate_main_info_table(doc, trip)
        self._generate_main_content_table(doc, trip)
        self._generate_signature_section(doc)

        return doc

    def _generate_header_section(self, doc):
        """Generate header section with company info and government heading"""
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        # Header Table
        header_table = doc.add_table(rows=1, cols=2)
        header_table.style = 'Table Grid'
        header_table.alignment = WD_TABLE_ALIGNMENT.LEFT

        # Remove table borders
        for row in header_table.rows:
            for cell in row.cells:
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9.5)

        # Left cell - Company info
        company_cell = header_table.cell(0, 0)
        # Clear all paragraphs first
        for paragraph in company_cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        company_para = company_cell.add_paragraph()
        title_run = company_para.add_run("1. Thông tin về đơn vị kinh doanh")
        title_run.bold = True
        company_para.add_run("\nĐơn vị vận tải: CHI NHÁNH CÔNG TY CP TIẾP VẬN HP TẠI TP. HẢI PHÒNG")
        company_para.add_run("\nĐịa chỉ: Room 202A, Dau Khi Hotel, 441 Da Nang Street, Hai An, Hai Phong, Vietnam")
        company_para.add_run("\nTel: +84 225 3556133 Fax: + 84 225 3556132")

        # Right cell - Government heading
        gov_cell = header_table.cell(0, 1)
        # Clear all paragraphs first
        for paragraph in gov_cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        gov_para = gov_cell.add_paragraph()
        gov_para.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
        gov_para.add_run("\nĐộc lập - Tự do - Hạnh phúc")
        gov_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _generate_main_info_table(self, doc, trip):
        """Generate main info table with driver info and document title"""
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        # Create table with 3 columns for title, info, and driver info
        info_table = doc.add_table(rows=2, cols=3)
        info_table.style = 'Table Grid'
        info_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Remove table borders
        for row in info_table.rows:
            for cell in row.cells:
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9.5)

        # Merge first column across both rows
        info_table.cell(0, 0).merge(info_table.cell(1, 0))
        driver_cell = info_table.cell(0, 0)
        # Clear all paragraphs first
        for paragraph in driver_cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        # Add empty paragraphs to push content to bottom
        for i in range(4):  # Add 4 empty paragraphs to push content down
            driver_cell.add_paragraph()

        # Add driver info at the bottom
        driver_para = driver_cell.add_paragraph()
        title_run = driver_para.add_run("2. Thông tin về người lái xe")
        title_run.bold = True
        driver_para.add_run("\nTên tài xế: ")
        bold_run = driver_para.add_run(f"{trip.driver_id.name if trip.driver_id else 'Bùi Văn Thắng'}")
        bold_run.bold = True
        driver_para.add_run("\nSố điện thoại liên hệ: ")
        bold_run = driver_para.add_run(f"{getattr(trip.driver_id, 'phone', 'N/A')}")
        bold_run.bold = True

        # Merge 2nd and 3rd columns for the first row
        info_table.cell(0, 1).merge(info_table.cell(0, 2))
        title_cell = info_table.cell(0, 1)

        # Clear existing content and create paragraphs properly
        for paragraph in title_cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        # Add title paragraph
        title_para = title_cell.add_paragraph()
        title_run = title_para.add_run("GIẤY VẬN TẢI")
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run.bold = True
        title_run.font.size = Pt(14)

        # Add subtitle paragraph
        subtitle_para = title_cell.add_paragraph()
        subtitle_run = subtitle_para.add_run(
            "(Ban hành kèm theo Thông tư số: 63/2014/TT-BGTVT ngày 07 tháng 11 năm 2014 của Bộ trưởng Bộ giao thông vận tải)")
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Second row - Vehicle number and Document info
        vehicle_cell = info_table.cell(1, 1)
        # Clear all paragraphs first
        for paragraph in vehicle_cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        vehicle_cell.add_paragraph()
        vehicle_para = vehicle_cell.add_paragraph()
        vehicle_para.add_run("Số Xe: ")
        bold_run = vehicle_para.add_run(f"{trip.truck_id.name if trip.truck_id and trip.truck_id.name else ' '}")
        bold_run.bold = True
        vehicle_para.add_run("    ")
        vehicle_para.add_run("\nSố Rơ mooc: ")
        
        # Get trailer name - use trip.trailer_id if available, otherwise get from fleet.vehicle.hpl
        trailer_name = ' '
        if trip.trailer_id:
            trailer_name = trip.trailer_id.name
        elif trip.truck_id:
            # Get the fleet.vehicle.hpl record to access trailer_id
            hpl_vehicle = self.env['fleet.vehicle.hpl'].search([
                ('vehicle_id', '=', trip.truck_id.id)
            ], limit=1)
            if hpl_vehicle and hpl_vehicle.trailer_id:
                trailer_name = hpl_vehicle.trailer_id.name
        
        bold_run = vehicle_para.add_run(trailer_name)
        bold_run.bold = True

        info_cell = info_table.cell(1, 2)
        # Clear all paragraphs first
        for paragraph in info_cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        info_cell.add_paragraph()
        info_para = info_cell.add_paragraph()
        info_para.add_run("Số: ")
        bold_run = info_para.add_run(f"{trip.code or ' '}")
        bold_run.bold = True
        info_para.add_run("    ")
        info_para.add_run("\nNgày đóng/trả hàng: ")
        trip_date = trip.plan_line_id.date if trip.plan_line_id else fields.Datetime.now()
        bold_run = info_para.add_run(f"{trip_date.strftime('%d/%m/%Y %H:%M')}")
        bold_run.bold = True

    def _generate_main_content_table(self, doc, trip):
        """Generate main content table with outbound, inbound, and permit sections"""
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        # Main Table
        main_table = doc.add_table(rows=2, cols=3)
        main_table.style = 'Table Grid'
        main_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        hdr_cells = main_table.rows[0].cells
        # Clear all paragraphs first
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                p = paragraph._element
                p.getparent().remove(p)

        # Add bold headers
        hdr_para1 = hdr_cells[0].add_paragraph()
        title_run = hdr_para1.add_run("Hàng Đi")
        title_run.bold = True

        hdr_para2 = hdr_cells[1].add_paragraph()
        title_run = hdr_para2.add_run("Hàng Về")
        title_run.bold = True

        hdr_para3 = hdr_cells[2].add_paragraph()
        title_run = hdr_para3.add_run("Cấp Phép")
        title_run.bold = True

        detail_cells = main_table.rows[1].cells
        
        # Generate outbound content (Hàng Đi)
        self._generate_trip_section(doc, trip, detail_cells[0], is_outbound=True)
        
        # Generate inbound content (Hàng Về) - template
        self._generate_trip_section(doc, trip, detail_cells[1], is_outbound=False)
        
        # Generate permit section (Cấp Phép)
        self._generate_permit_section(doc, trip, detail_cells[2])

    def _generate_trip_section(self, doc, trip, cell, is_outbound=True):
        """Generate trip section content - reusable for both outbound and inbound"""
        from docx.oxml import parse_xml
        
        # Clear all paragraphs first
        for paragraph in cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        if is_outbound:
            # Outbound content with actual data
            self._add_booking_info(cell, trip, show_data=True)
            self._add_client_info(cell, trip, show_data=True)
            self._add_contract_info(cell, trip, show_data=True)
            self._add_trip_info(cell, trip, show_data=True)
            self._add_goods_info(cell, trip, show_data=True)
            self._add_notes(cell, trip, show_data=True)
        else:
            # Inbound content - template only
            self._add_booking_info(cell, trip, show_data=False)
            self._add_client_info(cell, trip, show_data=False)
            self._add_contract_info(cell, trip, show_data=False)
            self._add_trip_info(cell, trip, show_data=False)
            self._add_goods_info(cell, trip, show_data=False)
            self._add_notes(cell, trip, show_data=False)

        # Add top padding to the cell
        cell._tc.get_or_add_tcPr().append(parse_xml(
            r'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="20" w:type="dxa"/></w:tcMar>'))

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
            client_address = getattr(trip.plan_line_id.client_id, 'address', '') if trip.plan_line_id and trip.plan_line_id.client_id else ''
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
            route_info = trip.get_route_info()

            bold_run = content_para.add_run("")
            bold_run.bold = True
            content_para.add_run("\nSố bill/booking: ")
            bold_run = content_para.add_run(f"{route_info['booking_bill']}")
            bold_run.bold = True
            content_para.add_run("\nSố cont: ")
            bold_run = content_para.add_run(f"{trip.container_number or ' '}")
            bold_run.bold = True
            content_para.add_run("\nSố seal: ")
            bold_run = content_para.add_run(f"{trip.seal_number or ' '}")
            bold_run.bold = True
            content_para.add_run("\nLoại cont: ")
            bold_run = content_para.add_run(f"{route_info['container_info']}")
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

            route_info = trip.get_route_info()
            pickup_port = route_info['pickup_port']
            bold_run = content_para.add_run(f"{pickup_port}")
            bold_run.bold = True

            content_para.add_run("\nĐiểm giao hàng: ")
            delivery_port = route_info['delivery_port']
            bold_run = content_para.add_run(f"{delivery_port}")
            bold_run.bold = True

            content_para.add_run("\nNơi trả hàng: ")
            loading_location = route_info['loading_location']
            bold_run = content_para.add_run(f"{loading_location}")
            bold_run.bold = True

            #Nơi trả/lấy vỏ (Empty Depot)
            if trip.plan_type == 'import':
                content_para.add_run("\nNơi trả vỏ: ")
            else:
                content_para.add_run("\nNơi lấy vỏ: ")

            empty_depot = route_info['empty_depot']
            bold_run = content_para.add_run(f"{empty_depot}")
            bold_run.bold = True

            content_para.add_run("\nThời gian vận chuyển dự kiến:")
            content_para.add_run("\nBắt đầu từ : ")
            trip_date = trip.plan_line_id.date if trip.plan_line_id else fields.Datetime.now()
            etd_str = trip.plan_line_id.estimate_time_departure.strftime('%d/%m/%Y %H:%M') if trip.plan_line_id.estimate_time_departure else ' '
            bold_run = content_para.add_run(f"{etd_str}")
            bold_run.bold = True
            content_para.add_run("\nđến: ")
            eta_str = trip.plan_line_id.estimate_time_arrival.strftime('%d/%m/%Y %H:%M') if trip.plan_line_id.estimate_time_arrival else ' '
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
            content_para.add_run("\nNơi trả/lấy vỏ:")
            content_para.add_run("\nThời gian vận chuyển dự kiến:")
            content_para.add_run("\nBắt đầu từ: ")
            content_para.add_run("\nđến: ")
            content_para.add_run("\nTổng số km dự kiến: ")
            bold_run = content_para.add_run("")
            bold_run.bold = True
            content_para.add_run("\nLiên hệ:")

    def _add_goods_info(self, cell, trip, show_data=True):
        """Add goods information section"""
        para = cell.add_paragraph()
        title_run = para.add_run("6. Thông tin về hàng hóa")
        title_run.bold = True

        content_para = cell.add_paragraph()
        content_para.add_run("Tên hàng hóa: ")
        if show_data:
            route_info = trip.get_route_info()

            bold_run = content_para.add_run(f"{trip.goods_name or ' '}")
            bold_run.bold = True
            content_para.add_run("\nKhối lượng hàng hóa (tấn): ")
            bold_run = content_para.add_run(f"{route_info['goods_weight']}")
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
            route_info = trip.get_route_info()
            content_para = cell.add_paragraph()
            bold_run = content_para.add_run(f"{route_info['notes']}")
            bold_run.bold = True

    def _generate_permit_section(self, doc, trip, cell):
        """Generate permit section with fuel and cost information"""
        from docx.oxml import parse_xml
        
        # Clear all paragraphs first
        for paragraph in cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        # Add fuel info
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
        if road_fee == 0: road_fee = ''
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

        # Add loading/unloading info
        cell.add_paragraph()
        cell.add_paragraph()
        cell.add_paragraph()
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

    def _generate_signature_section(self, doc):
        """Generate signature section with approval signatures"""
        from docx.shared import Inches, Pt
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        # Signature table
        sig_table = doc.add_table(rows=1, cols=3)
        sig_table.style = 'Table Grid'
        sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Remove table borders and add top padding
        for row in sig_table.rows:
            for cell in row.cells:
                # Remove borders
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))
                # Add top padding
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    r'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="20" w:type="dxa"/></w:tcMar>'))
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9.5)

        sig_cells = sig_table.rows[0].cells

        # Clear cells and add bold titles
        for cell in sig_cells:
            for paragraph in cell.paragraphs:
                p = paragraph._element
                p.getparent().remove(p)

        # First cell - NHÂN VIÊN LÀM LỆNH
        sig_para1 = sig_cells[0].add_paragraph()
        title_run = sig_para1.add_run("NHÂN VIÊN LÀM LỆNH")
        title_run.bold = True
        sig_cells[0].add_paragraph()
        sig_cells[0].add_paragraph()
        sig_cells[0].add_paragraph()

        # Second cell - LÁI XE NHẬN LỆNH
        sig_para2 = sig_cells[1].add_paragraph()
        title_run = sig_para2.add_run("LÁI XE NHẬN LỆNH")
        title_run.bold = True
        sig_cells[1].add_paragraph()
        sig_cells[1].add_paragraph()
        sig_cells[1].add_paragraph()

        # Third cell - T/L GIÁM ĐỐC CÔNG TY
        sig_para3 = sig_cells[2].add_paragraph()
        title_run = sig_para3.add_run("T/L GIÁM ĐỐC CÔNG TY")
        title_run.bold = True
        sig_cells[2].add_paragraph()
        sig_cells[2].add_paragraph()
        sig_cells[2].add_paragraph()
