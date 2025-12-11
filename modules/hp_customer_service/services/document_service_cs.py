from odoo import models, fields, _
from odoo.exceptions import UserError
import xlsxwriter
import io
import base64
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

class DocumentServiceCs(models.AbstractModel):
    _name = 'hp.document.service.cs'
    _inherit = 'hp.document.service'
    _description = 'Document Service For Customer Service (DO/AN)'

    def generate_arrival_notice_excel(self, document):
        workbook, output = self._get_excel_workbook()
        sheet = workbook.add_worksheet('Arrival Notice')

        # 1. Định nghĩa Formats riêng cho AN
        formats = self._define_an_formats(workbook)

        # 2. Thiết lập cột
        self._set_an_columns(sheet)

        # 3. Vẽ Header (Logo, Tên công ty)
        self._write_an_header(sheet, document, formats)

        # 4. Vẽ Thông tin chung (Shipper, Cnee, Vessel...)
        self._write_an_general_info(sheet, document, formats)

        # 5. Vẽ Bảng hàng hóa
        last_row = self._write_an_cargo_table(sheet, document, formats, start_row=22)

        # 6. Vẽ Footer (Lưu ý, Ký tên)
        self._write_an_footer(sheet, workbook, last_row + 2)

        filename = f"Arrival_Notice_{document.document_number}.xlsx"
        return self._finalize_excel(workbook, output, filename)

    def _define_an_formats(self, workbook):
        font_name = 'Times New Roman'
        return {
            'title': workbook.add_format(
                {'bold': True, 'font_name': font_name, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'}),
            'header_center': workbook.add_format(
                {'bold': True, 'font_name': font_name, 'font_size': 10, 'align': 'center', 'valign': 'vcenter'}),
            'subtitle': workbook.add_format(
                {'bold': True, 'font_name': font_name, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'}),
            'label': workbook.add_format(
                {'bold': True, 'italic': True, 'font_name': font_name, 'font_size': 10, 'border': 1, 'align': 'left',
                 'valign': 'top', 'text_wrap': True}),
            'label_no_bottom': workbook.add_format(
                {'bold': True, 'italic': True, 'font_name': font_name, 'font_size': 10, 'top': 1, 'left': 1, 'right': 1,
                 'bottom': 0, 'align': 'left', 'valign': 'top', 'text_wrap': True}),
            'content': workbook.add_format(
                {'font_name': font_name, 'font_size': 11, 'border': 1, 'align': 'left', 'valign': 'top',
                 'text_wrap': True}),
            'content_no_top': workbook.add_format(
                {'font_name': font_name, 'font_size': 11, 'top': 0, 'left': 1, 'right': 1, 'bottom': 1, 'align': 'left',
                 'valign': 'top', 'text_wrap': True}),
            'content_center': workbook.add_format(
                {'font_name': font_name, 'font_size': 11, 'border': 1, 'align': 'center', 'valign': 'top',
                 'text_wrap': True}),
            'content_bold': workbook.add_format(
                {'bold': True, 'font_name': font_name, 'font_size': 11, 'border': 1, 'align': 'center',
                 'valign': 'vcenter', 'text_wrap': True}),
            'table_header': workbook.add_format(
                {'bold': True, 'font_name': font_name, 'font_size': 10, 'border': 1, 'align': 'center',
                 'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#FFFFFF'}),
            'footer_bold': workbook.add_format(
                {'bold': True, 'font_name': font_name, 'font_size': 10, 'valign': 'top'}),
            'footer_normal': workbook.add_format(
                {'font_name': font_name, 'font_size': 10, 'valign': 'top', 'text_wrap': True}),
            'date_italic': workbook.add_format(
                {'align': 'right', 'font_name': font_name, 'font_size': 11, 'italic': True})
        }

    def _set_an_columns(self, sheet):
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 28)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 15)

    def _write_an_header(self, sheet, document, f):
        # Logo
        if self.env.company.logo:
            image_data = io.BytesIO(base64.b64decode(self.env.company.logo))
            sheet.insert_image('A1', 'logo.png', {'image_data': image_data, 'x_scale': 0.8, 'y_scale': 0.8})

        sheet.merge_range('C1:F1', "CÔNG TY CP TIẾP VẬN HP", f['title'])
        sheet.merge_range('C2:F2', "HP LOGISTICS JOINT STOCK COMPANY", f['header_center'])
        sheet.merge_range('C3:F3', "Số 20 đường 2.5, Khu Đô Thị Gamuda Garden, Hoàng Mai, Hà Nội", f['header_center'])
        sheet.merge_range('C4:F4', "Tel: 0246 2941 086   Fax: 04 3734 7995", f['header_center'])

        sheet.merge_range('A6:F6', "GIẤY BÁO HÀNG ĐẾN", f['title'])
        sheet.merge_range('A7:F7', "(ARRIVAL NOTICE)", f['subtitle'])

    def _write_an_general_info(self, sheet, document, f):
        shipper_info = document.shipper_id.name if document.shipper_id else ''
        consignee_info = document.consignee_id.name if document.consignee_id else ''
        notify_info = document.notify_party_id.name if document.notify_party_id else ''
        bl_info = document.bl_number or ''
        vessel_info = f"{document.vessel_name or ''} / {document.voyage or ''}"
        eta_info = document.eta.strftime('%d/%m/%Y') if document.eta else ''

        # Row 9-13
        sheet.merge_range('A9:C9', "NGƯỜI GỬI HÀNG (Shipper):", f['label'])
        sheet.write('D9', "SỐ VẬN ĐƠN (B/L No):", f['label'])
        sheet.merge_range('E9:F9', bl_info, f['content_bold'])
        sheet.merge_range('A10:C13', shipper_info, f['content'])

        sheet.write('D10', "TÊN TÀU / CHUYẾN (Vol/Voy):", f['label_no_bottom'])
        sheet.merge_range('D11:D13', vessel_info, f['content_no_top'])

        sheet.merge_range('E10:F10', "NGÀY DỰ KIẾN TÀU ĐẾN (ETA):", f['label_no_bottom'])
        sheet.merge_range('E11:F16', eta_info, f['content_no_top'])

        # Row 14-18
        sheet.merge_range('A14:C14', "NGƯỜI NHẬN HÀNG (Consignee):", f['label'])
        sheet.write('D14', "TÀU NỐI / CHUYẾN (Connecting Vol/Voy):", f['label_no_bottom'])
        sheet.merge_range('A15:C18', consignee_info, f['content'])
        sheet.merge_range('D15:D16', "", f['content_no_top'])

        sheet.write('D17', "Nơi nhận hàng (Place of receipt)", f['label'])
        sheet.merge_range('E17:F17', "CẢNG XẾP (Port of loading)", f['label'])
        sheet.write('D18', document.place_of_receipt or '', f['content'])
        sheet.merge_range('E18:F18', document.pol_id.name or '', f['content'])

        # Row 19-22
        sheet.merge_range('A19:C19', "NGƯỜI THÔNG BÁO (Notify Party):", f['label'])
        sheet.write('D19', "CẢNG DỠ (Port of discharge)", f['label'])
        sheet.merge_range('E19:F19', "NƠI GIAO HÀNG (Place of delivery)", f['label'])
        sheet.merge_range('A20:C22', notify_info, f['content'])
        sheet.merge_range('D20:D22', document.pod_id.name or '', f['content'])
        sheet.merge_range('E20:F22', document.place_of_delivery or '', f['content'])

    def _write_an_cargo_table(self, sheet, document, f, start_row):
        r = start_row
        sheet.merge_range(r, 0, r, 1, "SỐ CONT CHÌ\nMarks & Nos./Container No./ Seal No.", f['table_header'])
        sheet.write(r, 2, "SỐ KIỆN\nNo. of Packages", f['table_header'])
        sheet.write(r, 3, "ĐẶC ĐIỂM HÀNG HÓA\nDescription of Goods", f['table_header'])
        sheet.write(r, 4, "TRỌNG LƯỢNG\nGross weight(KGM)", f['table_header'])
        sheet.write(r, 5, "KÍCH THƯỚC\nMeasurement", f['table_header'])

        r += 1
        for line in document.container_line_ids:
            cont_seal = f"{line.container_number or ''}\n{line.seal_number or ''}"
            sheet.merge_range(r, 0, r, 1, cont_seal, f['content_center'])
            sheet.write(r, 2, line.packages or '', f['content_center'])
            sheet.write(r, 3, line.goods_description or '', f['content_center'])
            sheet.write(r, 4, f"{line.gross_weight:,.2f}" if line.gross_weight else '', f['content_center'])
            sheet.write(r, 5, line.measurement or '', f['content_center'])
            r += 1

        # Dòng trống cuối bảng
        for i in range(6):
            if i == 0:
                sheet.merge_range(r, 0, r, 1, "........................", f['content_center'])
            elif i > 1:
                sheet.write(r, i, "........................", f['content_center'])

        return r

    def _write_an_footer(self, sheet, workbook, start_row):
        r = start_row
        f = self._define_an_formats(workbook)

        sheet.write(r, 0, "Kính mời Quý khách đến:", f['footer_bold'])
        sheet.merge_range(r, 1, r, 5, "Chi nhánh Công ty cổ phần tiếp vận HP tại Hải Phòng", f['footer_bold'])
        r += 1
        sheet.write(r, 0, "", workbook.add_format({'left': 1, 'right': 1}))
        sheet.merge_range(r, 1, r, 5, "Phòng 201+202, khách sạn Dầu Khí, 441 đường Đà Nẵng, Hải An, Hải Phòng",
                          f['footer_normal'])
        r += 1
        sheet.write(r, 0, "", workbook.add_format({'left': 1, 'right': 1, 'bottom': 1}))
        sheet.merge_range(r, 1, r, 5, "Tel: +84.225.3556133",
                          workbook.add_format({'bottom': 1, 'font_name': 'Times New Roman', 'font_size': 10}))

        r += 2
        sheet.write(r, 0, "Khi đến cần mang theo:", f['footer_bold'])
        sheet.write(r, 1, "1", f['footer_normal'])
        sheet.write(r, 2, "Giấy giới thiệu", f['footer_normal'])
        sheet.merge_range(r, 3, r, 5, "2. Thanh toán cước và phụ phí (nếu có)", f['footer_normal'])
        r += 1
        sheet.write(r, 1, "3", f['footer_normal'])
        sheet.write(r, 2, "Căn cước công dân", f['footer_normal'])
        sheet.merge_range(r, 3, r, 5, "4. Trường hợp nhận ủy thác phải có giấy ủy quyền bản gốc", f['footer_normal'])
        r += 1
        sheet.write(r, 1, "5", f['footer_normal'])
        sheet.write(r, 2, "Bill gốc (nếu có)", f['footer_normal'])

        r += 1
        sheet.write(r, 0, "XIN LƯU Ý", f['footer_bold'])
        sheet.merge_range(r, 1, r, 5,
                          "Trước khi đến nhận Lệnh giao hàng, vui lòng liên hệ với chúng tôi theo số: +84.225.3556133",
                          f['footer_normal'])

        r += 2
        today = fields.Date.today()
        date_str = f"Hải Phòng, ngày {today.day} tháng {today.month} năm {today.year}"
        sheet.merge_range(r, 3, r, 5, date_str, f['date_italic'])

    def generate_delivery_order_word(self, document):
        doc = self._get_docx_document()
        self._configure_docx_page(doc)

        # 1. Header (Logo & Company Info)
        self._add_do_header(doc)

        # 2. Tiêu đề và Kính gửi
        self._add_do_title_section(doc, document)

        # 3. Thông tin Consignee và B/L
        self._add_do_consignee_info(doc, document)

        # 4. Bảng thông tin MBL/Vessel/Route
        self._add_do_shipment_details(doc, document)

        # 5. Bảng hàng hóa
        self._add_do_cargo_table(doc, document)

        # 6. Footer (Lưu ý & Ký nhận)
        self._add_do_footer(doc, document)

        filename = f"Delivery_Order_{document.document_number}.docx"
        return self._finalize_docx(doc, filename)

    def _configure_docx_page(self, doc):
        section = doc.sections[0]
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(1.5)
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(11)

    def _add_do_header(self, doc):
        header_table = doc.add_table(rows=1, cols=2)
        header_table.autofit = False
        header_table.columns[0].width = Cm(4)
        header_table.columns[1].width = Cm(13)

        # Logo
        cell_logo = header_table.cell(0, 0)
        p_logo = cell_logo.paragraphs[0]
        if self.env.company.logo:
            image_data = io.BytesIO(base64.b64decode(self.env.company.logo))
            p_logo.add_run().add_picture(image_data, width=Cm(3.5))

        # Company Info
        cell_info = header_table.cell(0, 1)
        p_info = cell_info.paragraphs[0]
        r1 = p_info.add_run("CÔNG TY CỔ PHẦN TIẾP VẬN HP\n")
        r1.bold = True
        r1.font.size = Pt(13)
        p_info.add_run(
            "VP-1A 3rd Floor, GreenPearl Building, No. 378 Minh Khai Ward, Vinh Tuy, Hai Ba Trung, Hanoi, Vietnam\n")
        p_info.add_run("Tel: (84-4) 3848 9189 - Fax: (84-4) 3734 7995\n")
        p_info.add_run("Email: cs@hplogistics.com.vn")

        # Line separator
        p_line = doc.add_paragraph()
        p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_line.add_run("_" * 80).bold = True

    def _add_do_title_section(self, doc, document):
        p_title = doc.add_paragraph("\nLỆNH GIAO HÀNG\n(Delivery Order)")
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p_title.runs:
            r.bold = True
            r.font.size = Pt(16)

        doc.add_paragraph(f"Số (No.): {document.document_number}").alignment = WD_ALIGN_PARAGRAPH.CENTER

        port_name = document.pod_id.name if document.pod_id else "........................................"
        p_to = doc.add_paragraph()
        p_to.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_to.add_run("\nKính gửi: ").bold = True
        p_to.add_run(f"CẢNG {port_name.upper()}\n").bold = True
        p_to.add_run("Đồng kính gửi: ").bold = True
        p_to.add_run("CÁC CƠ QUAN HỮU QUAN.")

    def _add_do_consignee_info(self, doc, document):
        consignee_name = document.consignee_id.name if document.consignee_id else "........................"
        p_deliver = doc.add_paragraph()
        p_deliver.add_run("\nTrân trọng đề nghị giao lô hàng sau cho: ")
        p_deliver.add_run(f"{consignee_name}").bold = True

        doc.add_paragraph("Please deliver the following merchandise to")
        p_bl = doc.add_paragraph()
        p_bl.add_run("Số Vận đơn: ").bold = True
        p_bl.add_run(document.bl_number or "")

    def _add_do_shipment_details(self, doc, document):
        info_table = doc.add_table(rows=3, cols=2)
        info_table.autofit = True

        # Row 1: MBL / HBL
        c1 = info_table.cell(0, 0)
        c2 = info_table.cell(0, 1)
        c1.text = f"Số MBL: {document.mbl_number or ''}"
        c2.text = f"HBL: {document.hbl_number or ''}"
        c1.paragraphs[0].runs[0].bold = True

        # Row 2: Vessel
        c1 = info_table.cell(1, 0)
        c2 = info_table.cell(1, 1)
        c1.merge(c2)
        p_vessel = c1.paragraphs[0]
        p_vessel.add_run("Lô hàng kê khai dưới đây ở tàu: ")
        p_vessel.add_run(f"{document.vessel_name or ''}").bold = True
        p_vessel.add_run(f"\tChuyến: {document.voyage or ''}")
        p_vessel.add_run("\nVessel Name")

        # Row 3: Route
        c1 = info_table.cell(2, 0)
        c2 = info_table.cell(2, 1)
        c1.merge(c2)
        p_route = c1.paragraphs[0]
        p_route.add_run(f"Từ: {document.pol_id.name or ''}\t\tđến: {document.pod_id.name or ''}")
        eta_str = document.eta.strftime('%d/%m/%Y') if document.eta else "................"
        p_route.add_run(f"\t\tNgày đến: {eta_str}")
        p_route.add_run("\nFrom\t\t\t\tto\t\t\t\tArrival Date")
        p_route.paragraph_format.space_after = Pt(0)

    def _add_do_cargo_table(self, doc, document):
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'

        # Header
        headers = [
            "SỐ CONTAINER;\nSỐ SEAL\nMarks and Nos; Container/Seal No.",
            "SỐ KIỆN\nNo. of Package",
            "KÝ MÃ HIỆU\nTÊN HÀNG HÓA\nDescription of Goods",
            "TRỌNG LƯỢNG (KGM)\nGross Weight",
            "KÍCH THƯỚC (M3)\nMeasurement"
        ]
        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            cell = hdr_cells[i]
            cell.text = h
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.bold = True
                    r.font.size = Pt(10)

        # Body
        for line in document.container_line_ids:
            row_cells = table.add_row().cells
            row_cells[0].text = f"{line.container_number or ''}\n{line.seal_number or ''}"
            row_cells[1].text = str(line.packages or '')
            row_cells[2].text = line.goods_description or ''
            row_cells[3].text = f"{line.gross_weight:,.2f}" if line.gross_weight else ""
            row_cells[4].text = str(line.measurement) if line.measurement else ""

            for cell in row_cells:
                # Center align all except description maybe? keeping simple
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_do_footer(self, doc, document):
        p_note1 = doc.add_paragraph("LƯU Ý: Xin quý khách vui lòng đối chiếu chi tiết hàng khi nhận lệnh giao hàng.")
        p_note1.paragraph_format.space_before = Pt(12)
        p_note1.paragraph_format.space_after = Pt(0)

        doc.add_paragraph("Rất cảm ơn sự hợp tác và ủng hộ của Quý khách hàng.")

        # Date
        p_date = doc.add_paragraph()
        p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        today = fields.Date.today()
        today_str = f"................., ngày {today.day} tháng {today.month} năm {today.year}"
        p_date.add_run(today_str).bold = True

        # Signatures
        sign_table = doc.add_table(rows=1, cols=2)
        sign_table.autofit = False
        sign_table.columns[0].width = Cm(11)
        sign_table.columns[1].width = Cm(8)

        # Left: Signature
        c_left = sign_table.cell(0, 0)
        p_left = c_left.paragraphs[0]
        p_left.add_run("Ký nhận đủ bộ chứng từ\n").bold = True
        p_left.add_run("Ngày:.......................\n")

        # Contact Info
        contact_name = document.contact_name or "..................................."
        contact_phone = document.contact_phone or "......................."
        contact_tax = document.contact_tax_code or "........................"
        p_left.add_run(f"Họ và tên: {contact_name}\n")
        p_left.add_run(f"Số điện thoại: {contact_phone}\n")
        p_left.add_run(f"Mã số thuế: {contact_tax}")