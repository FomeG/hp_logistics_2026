from odoo import models, fields, api
from odoo.addons.hp_components.models import constants
import xlsxwriter
import io
import base64
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm


class CsShippingDocument(models.Model):
    _name = "cs.shipping.document"
    _inherit = ['cs.order.detail', 'mail.thread', 'mail.activity.mixin']
    _description = "Customer Service Shipping Document"

    name = fields.Char(
        required=True,
        readonly=True,
        store=True,
        compute='_compute_name',
        tracking=True,
    )

    instruction_type = fields.Selection(
        constants.ShippingDocumentType.SELECT_OPTIONS,
        required=True,
        string="Instruction Type",
        tracking=True,
    )
    document_number = fields.Char(
        string="DO/AN Number",
        required=True,
        tracking=True,
        help="Delivery Order (DO) or Arrival Notice (AN) number",
    )


    state = fields.Selection(
        constants.ShippingDocumentState.SELECT_OPTIONS,
        string="State",
        default=constants.ShippingDocumentState.DRAFT,
        tracking=True,
        required=True,
    )

    note = fields.Text(
        string="Note",
        tracking=True,
    )

    cs_shipping_instruction_id = fields.Many2one(
        comodel_name='cs.shipping.instruction',
        string="Related Shipping Instruction",
        compute='_compute_shipping_instruction',
        store= True,
    )

    shipper_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipper',
        required=True,
        related='cs_shipping_instruction_id.shipper',
        store=True,
        readonly=False,
        help='Thông tin bên gửi hàng'
    )

    consignee_id = fields.Many2one(
        comodel_name='res.partner',
        string='Consignee',
        required=True,
        related='cs_shipping_instruction_id.consignee',
        store=True,
        readonly=False,
    )

    notify_party_id = fields.Many2one(
        comodel_name='res.partner',
        string='Notify Party',
        related='cs_shipping_instruction_id.notify_party',
        store=True,
        readonly=False,
    )

    contact_name = fields.Char(
        string="Contact Name",
        compute='_compute_contact_info',
        store=True,
        readonly=False,
        tracking=True,
    )

    contact_phone = fields.Char(
        string="Contact Phone",
        compute='_compute_contact_info',
        store=True,
        readonly=False,
        tracking=True,
    )

    contact_tax_code = fields.Char(
        string='MST',
        compute='_compute_contact_info',
        store=True,
        readonly=False,
        help='Mã số thuế (mặc định lấy từ client)'
    )

    cs_bill_lading_id = fields.Many2one(
        comodel_name='cs.bill.lading',
        string="Bill of Lading",
        compute='_compute_bill_lading_info',
        domain="[('cs_order_id', '=', cs_order_id)]",
        tracking=True,
    )

    issue_date = fields.Date(
        string="Issue Date",
        related='cs_bill_lading_id.issue_date',
        tracking=True,
    )

    bl_number = fields.Char(
        string="BL Number",
        tracking=True,
        related='cs_bill_lading_id.bl_number',
        store=True,
    )

    mbl_number = fields.Char(
        string="Master Bill of Lading Number",
        tracking=True,
    )
    hbl_number = fields.Char(
        string="House Bill of Lading Number",
        tracking=True,
    )

    vessel_name = fields.Char(
        string='Vessel Name',
        related='booking_id.vessel_id.name',
        store=True,
        help='Vessel Name from Booking',
    )

    voyage = fields.Char(
        string='Voyage',
        related='booking_id.voyage',
        store=True,
        help='Voyage from Booking',
    )

    pol_id = fields.Many2one(
        comodel_name='location.base',
        string='Port of Loading',
        related='booking_id.from_location_id',
        store=True,
    )

    pod_id = fields.Many2one(
        comodel_name='location.base',
        string='Port of Discharge',
        related='booking_id.to_location_id',
        store=True,
    )

    place_of_receipt = fields.Char(
        string='Place of Receipt',
        related='cs_shipping_instruction_id.place_of_receipt',
        store=True,
    )

    place_of_delivery = fields.Char(
        string='Place of Delivery',
        compute='_compute_place_of_delivery',
        store=True,
        readonly=True,
    )

    etd = fields.Date(
        string='Estimate of Departure',
        related='booking_id.etd',
        store=True,
    )

    eta = fields.Datetime(
        string='Estimate of Arrival',
        related='cs_order_id.estimate_time_arrival',
        store=True,
    )

    container_line_ids = fields.One2many(
        comodel_name='cs.container',
        inverse_name='shipping_document_id',
        string='Danh sách Container',
        required=True,
        help='Chi tiết container cần giao'
    )

    def _get_company_logo_stream(self):
        if self.env.company.logo:
            image_data = base64.b64decode(self.env.company.logo)
            return io.BytesIO(image_data)
        return None

    @api.depends('cs_order_id', 'cs_order_id.cs_bill_lading_ids',
                 'cs_order_id.cs_bill_lading_ids.issue_date')
    def _compute_bill_lading_info(self):
        for record in self:
            bls = record.cs_order_id.cs_bill_lading_ids

            if bls:
                first_bl = bls[0]
                record.cs_bill_lading_id = first_bl.id
            else:
                record.cs_bill_lading_id = False

    @api.depends('cs_order_id', 'cs_order_id.cs_shipping_instruction_id')
    def _compute_shipping_instruction(self):
        for record in self:
            if record.cs_order_id and record.cs_order_id.cs_shipping_instruction_id:
                # cs_shipping_instruction_id là One2many nên lấy record đầu tiên
                shipping_instructions = record.cs_order_id.cs_shipping_instruction_id
                if shipping_instructions:
                    record.cs_shipping_instruction_id = shipping_instructions[0].id
                else:
                    record.cs_shipping_instruction_id = False
            else:
                record.cs_shipping_instruction_id = False

    @api.depends('document_number')
    def _compute_name(self):
        for record in self:
            record.name = record.document_number

    @api.depends('cs_order_id', 'cs_order_id.service_type',
                 'cs_order_id.goods_delivery_location_id',
                 'cs_order_id.actual_destination_location_id')
    def _compute_place_of_delivery(self):
        """
        Export → actual_destination_location_id (cảng/depot đích)
        Import → goods_delivery_location_id (nơi giao hàng cho khách)
        """
        for record in self:
            if not record.cs_order_id:
                record.place_of_delivery = False
                continue

            cs_order = record.cs_order_id

            if cs_order.service_type == 'export':
                location = cs_order.actual_destination_location_id
            else:
                location = cs_order.goods_delivery_location_id

            record.place_of_delivery = location.name if location else False

    @api.depends('cs_order_id')
    def _compute_contact_info(self):
        for record in self:
            client = record.cs_order_id.sale_order_id.client_id
            if client:
                record.contact_name = client.name
                record.contact_phone = client.phone
                record.contact_tax_code = client.vat if hasattr(client, 'vat') else False
            else:
                record.contact_name = False
                record.contact_phone = False
                record.contact_tax_code = False

    def action_export_an_excel(self):
        self.ensure_one()
        if self.instruction_type != 'arrival_notice':
            raise UserError("Chức năng này chỉ dành cho Arrival Notice.")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Arrival Notice')

        # 1. ĐỊNH DẠNG (STYLES)
        font_name = 'Times New Roman'

        f_title = workbook.add_format({
            'bold': True, 'font_name': font_name, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'
        })
        f_header_center = workbook.add_format({
            'bold': True, 'font_name': font_name, 'font_size': 10, 'align': 'center', 'valign': 'vcenter'
        })
        f_subtitle = workbook.add_format({
            'bold': True, 'font_name': font_name, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'
        })

        # STYLES CELL
        f_label = workbook.add_format({
            'bold': True, 'italic': True, 'font_name': font_name, 'font_size': 10,
            'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True
        })

        f_label_no_bottom = workbook.add_format({
            'bold': True, 'italic': True, 'font_name': font_name, 'font_size': 10,
            'top': 1, 'left': 1, 'right': 1, 'bottom': 0,
            'align': 'left', 'valign': 'top', 'text_wrap': True
        })

        f_content = workbook.add_format({
            'font_name': font_name, 'font_size': 11,
            'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True
        })

        f_content_no_top = workbook.add_format({
            'font_name': font_name, 'font_size': 11,
            'top': 0, 'left': 1, 'right': 1, 'bottom': 1,
            'align': 'left', 'valign': 'top', 'text_wrap': True
        })

        f_content_center = workbook.add_format({
            'font_name': font_name, 'font_size': 11,
            'border': 1, 'align': 'center', 'valign': 'top', 'text_wrap': True
        })

        f_content_bold = workbook.add_format({
            'bold': True, 'font_name': font_name, 'font_size': 11,
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })

        f_table_header = workbook.add_format({
            'bold': True, 'font_name': font_name, 'font_size': 10,
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
            'bg_color': '#FFFFFF'
        })

        f_footer_bold = workbook.add_format({'bold': True, 'font_name': font_name, 'font_size': 10, 'valign': 'top'})
        f_footer_normal = workbook.add_format(
            {'font_name': font_name, 'font_size': 10, 'valign': 'top', 'text_wrap': True})

        # 2. THIẾT LẬP CỘT
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 28)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 15)

        # 3. HEADER
        logo_stream = self._get_company_logo_stream()
        if logo_stream:
            sheet.insert_image('A1', 'logo.png', {'image_data': logo_stream, 'x_scale': 0.8, 'y_scale': 0.8})

        sheet.merge_range('C1:F1', "CÔNG TY CP TIẾP VẬN HP", f_title)
        sheet.merge_range('C2:F2', "HP LOGISTICS JOINT STOCK COMPANY", f_header_center)
        sheet.merge_range('C3:F3', "Số 20 đường 2.5, Khu Đô Thị Gamuda Garden, Hoàng Mai, Hà Nội", f_header_center)
        sheet.merge_range('C4:F4', "Tel: 0246 2941 086   Fax: 04 3734 7995", f_header_center)

        sheet.merge_range('A6:F6', "GIẤY BÁO HÀNG ĐẾN", f_title)
        sheet.merge_range('A7:F7', "(ARRIVAL NOTICE)", f_subtitle)

        # 4. DATA BODY
        shipper_info = self.shipper_id.name if self.shipper_id else ''
        consignee_info = self.consignee_id.name if self.consignee_id else ''
        notify_info = self.notify_party_id.name if self.notify_party_id else ''

        bl_info = self.bl_number or ''
        vessel_info = f"{self.vessel_name or ''} / {self.voyage or ''}"
        eta_info = self.eta.strftime('%d/%m/%Y') if self.eta else ''

        # --- KHỐI 1 (Row 9-13) ---
        sheet.merge_range('A9:C9', "NGƯỜI GỬI HÀNG (Shipper):", f_label)
        sheet.write('D9', "SỐ VẬN ĐƠN (B/L No):", f_label)
        sheet.merge_range('E9:F9', bl_info, f_content_bold)

        sheet.merge_range('A10:C13', shipper_info, f_content)

        # Cột D: Tên Tàu (Label no bottom + Content no top)
        sheet.write('D10', "TÊN TÀU / CHUYẾN (Vol/Voy):", f_label_no_bottom)
        sheet.merge_range('D11:D13', vessel_info, f_content_no_top)

        # Cột E-F: ETA Label (Label no bottom)
        sheet.merge_range('E10:F10', "NGÀY DỰ KIẾN TÀU ĐẾN (ETA):", f_label_no_bottom)

        # Content no top để nối với Label ở Row 10
        sheet.merge_range('E11:F16', eta_info, f_content_no_top)

        # KHỐI 2 (Row 14-18)
        # Label Consignee
        sheet.merge_range('A14:C14', "NGƯỜI NHẬN HÀNG (Consignee):", f_label)

        # Cột D: Label Tàu Nối
        sheet.write('D14', "TÀU NỐI / CHUYẾN (Connecting Vol/Voy):", f_label_no_bottom)
        # Consignee Info (Gộp dọc xuống)
        sheet.merge_range('A15:C18', consignee_info, f_content)
        # Cột D: Value Tàu Nối
        sheet.merge_range('D15:D16', "", f_content_no_top)
        # Row 17-18: Receipt / POL
        sheet.write('D17', "Nơi nhận hàng (Place of receipt)", f_label)
        sheet.merge_range('E17:F17', "CẢNG XẾP (Port of loading)", f_label)

        sheet.write('D18', self.place_of_receipt or '', f_content)
        sheet.merge_range('E18:F18', self.pol_id.name or '', f_content)

        # KHỐI 3 (Row 19-22)
        sheet.merge_range('A19:C19', "NGƯỜI THÔNG BÁO (Notify Party):", f_label)
        sheet.write('D19', "CẢNG DỠ (Port of discharge)", f_label)
        sheet.merge_range('E19:F19', "NƠI GIAO HÀNG (Place of delivery)", f_label)

        sheet.merge_range('A20:C22', notify_info, f_content)
        sheet.merge_range('D20:D22', self.pod_id.name or '', f_content)
        sheet.merge_range('E20:F22', self.place_of_delivery or '', f_content)

        # 5. BẢNG HÀNG HÓA
        r = 22
        sheet.merge_range(r, 0, r, 1, "SỐ CONT CHÌ\nMarks & Nos./Container No./ Seal No.", f_table_header)
        sheet.write(r, 2, "SỐ KIỆN\nNo. of Packages", f_table_header)
        sheet.write(r, 3, "ĐẶC ĐIỂM HÀNG HÓA\nDescription of Goods", f_table_header)
        sheet.write(r, 4, "TRỌNG LƯỢNG\nGross weight(KGM)", f_table_header)
        sheet.write(r, 5, "KÍCH THƯỚC\nMeasurement", f_table_header)

        r += 1
        for line in self.container_line_ids:
            cont_seal = f"{line.container_number or ''}\n{line.seal_number or ''}"
            sheet.merge_range(r, 0, r, 1, cont_seal, f_content_center)
            sheet.write(r, 2, line.packages or '', f_content_center)
            sheet.write(r, 3, line.goods_description or '', f_content_center)
            sheet.write(r, 4, f"{line.gross_weight:,.2f}" if line.gross_weight else '', f_content_center)
            sheet.write(r, 5, line.measurement or '', f_content_center)
            r += 1

        sheet.merge_range(r, 0, r, 1, "........................", f_content_center)
        sheet.write(r, 2, "........................", f_content_center)
        sheet.write(r, 3, "........................", f_content_center)
        sheet.write(r, 4, "........................", f_content_center)
        sheet.write(r, 5, "........................", f_content_center)

        r += 2
        # 6. FOOTER
        sheet.write(r, 0, "Kính mời Quý khách đến:", f_footer_bold)
        sheet.merge_range(r, 1, r, 5, "Chi nhánh Công ty cổ phần tiếp vận HP tại Hải Phòng", f_footer_bold)
        r += 1
        sheet.write(r, 0, "", workbook.add_format({'left': 1, 'right': 1}))
        sheet.merge_range(r, 1, r, 5, "Phòng 201+202, khách sạn Dầu Khí, 441 đường Đà Nẵng, Hải An, Hải Phòng",
                          f_footer_normal)
        r += 1
        sheet.write(r, 0, "", workbook.add_format({'left': 1, 'right': 1, 'bottom': 1}))
        sheet.merge_range(r, 1, r, 5, "Tel: +84.225.3556133",
                          workbook.add_format({'bottom': 1, 'font_name': font_name, 'font_size': 10}))

        r += 2
        sheet.write(r, 0, "Khi đến cần mang theo:", f_footer_bold)
        sheet.write(r, 1, "1", f_footer_normal)
        sheet.write(r, 2, "Giấy giới thiệu", f_footer_normal)
        sheet.merge_range(r, 3, r, 5, "2. Thanh toán cước và phụ phí (nếu có)", f_footer_normal)
        r += 1
        sheet.write(r, 1, "3", f_footer_normal)
        sheet.write(r, 2, "Căn cước công dân", f_footer_normal)
        sheet.merge_range(r, 3, r, 5, "4. Trường hợp nhận ủy thác phải có giấy ủy quyền bản gốc", f_footer_normal)
        r += 1
        sheet.write(r, 1, "5", f_footer_normal)
        sheet.write(r, 2, "Bill gốc (nếu có)", f_footer_normal)

        r += 1
        sheet.write(r, 0, "XIN LƯU Ý", f_footer_bold)
        sheet.merge_range(r, 1, r, 5,
                          "Trước khi đến nhận Lệnh giao hàng, vui lòng liên hệ với chúng tôi theo số: +84.225.3556133",
                          f_footer_normal)
        r += 1
        sheet.merge_range(r, 1, r, 5, "Vui lòng lấy lệnh giao hàng sau 1 ngày từ ngày đến cho hàng lẻ (LCL)",
                          f_footer_normal)
        r += 1
        sheet.merge_range(r, 1, r, 5, "và ngày tàu đến cho hàng nguyên cont (FCL)", f_footer_normal)
        r += 1
        sheet.merge_range(r, 1, r, 5,
                          "Thông tin trên Giấy báo chỉ là dự kiến, Quý khách vui lòng mở tờ khai sau ngày tàu vào.",
                          f_footer_normal)

        r += 2
        today = fields.Date.today()
        date_str = f"Hải Phòng, ngày {today.day} tháng {today.month} năm {today.year}"
        sheet.merge_range(r, 3, r, 5, date_str, workbook.add_format(
            {'align': 'right', 'font_name': font_name, 'font_size': 11, 'italic': True}))

        workbook.close()
        output.seek(0)

        return self._create_attachment_download(output.read(), f'Arrival_Notice_{self.document_number}.xlsx', 'xlsx')

    def action_export_do_word(self):
        self.ensure_one()
        if self.instruction_type != 'delivery_order':
            raise UserError("Chức năng này chỉ dành cho Delivery Order.")

        if not Document:
            raise UserError("Vui lòng cài đặt thư viện python-docx (pip install python-docx)")

        doc = Document()

        # CẤU HÌNH TRANG & FONT
        section = doc.sections[0]
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(1.5)

        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(11)

        # 1. HEADER (LOGO & INFO)
        header_table = doc.add_table(rows=1, cols=2)
        header_table.autofit = False
        header_table.allow_autofit = False
        header_table.columns[0].width = Cm(4)  # Cột Logo
        header_table.columns[1].width = Cm(13)  # Cột Info

        # Insert Logo
        cell_logo = header_table.cell(0, 0)
        p_logo = cell_logo.paragraphs[0]
        logo_stream = self._get_company_logo_stream()
        if logo_stream:
            p_logo.add_run().add_picture(logo_stream, width=Cm(3.5))

        # Insert Company Info
        cell_info = header_table.cell(0, 1)
        p_info = cell_info.paragraphs[0]
        r1 = p_info.add_run("CÔNG TY CỔ PHẦN TIẾP VẬN HP\n")
        r1.bold = True
        r1.font.size = Pt(13)

        # Địa chỉ (lấy từ self.env.company)
        p_info.add_run(
            "VP-1A 3rd Floor, GreenPearl Building, No. 378 Minh Khai Ward, Vinh Tuy, Hai Ba Trung, Hanoi, Vietnam\n")
        p_info.add_run("Tel: (84-4) 3848 9189 - Fax: (84-4) 3734 7995\n")
        p_info.add_run("Email: cs@hplogistics.com.vn")

        # Kẻ đường gạch ngang
        p_line = doc.add_paragraph()
        p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_line.add_run("_" * 80).bold = True

        # 2. TITLE
        p_title = doc.add_paragraph("\nLỆNH GIAO HÀNG\n(Delivery Order)")
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p_title.runs:
            r.bold = True
            r.font.size = Pt(16)

        doc.add_paragraph(f"Số (No.): {self.document_number}").alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 3. KÍNH GỬI
        # Lấy tên cảng từ POD
        port_name = self.pod_id.name if self.pod_id else "........................................"

        p_to = doc.add_paragraph()
        p_to.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_to.add_run("\nKính gửi: ").bold = True
        p_to.add_run(f"CẢNG {port_name.upper()}\n").bold = True  # Chữ hoa cho đẹp
        p_to.add_run("Đồng kính gửi: ").bold = True
        p_to.add_run("CÁC CƠ QUAN HỮU QUAN.")

        # 4. GIAO HÀNG CHO
        consignee_name = self.consignee_id.name if self.consignee_id else "........................"
        p_deliver = doc.add_paragraph()
        p_deliver.add_run("\nTrân trọng đề nghị giao lô hàng sau cho: ")
        p_deliver.add_run(f"{consignee_name}").bold = True

        p_intro = doc.add_paragraph("Please deliver the following merchandise to")
        p_bl = doc.add_paragraph()
        p_bl.add_run("Số Vận đơn: ").bold = True
        p_bl.add_run(self.bl_number or "")
        # 5. INFO BLOCK (MBL/HBL)
        info_table = doc.add_table(rows=3, cols=2)
        info_table.autofit = True

        # Row 1: BL/ MBL / HBL
        c1 = info_table.cell(0, 0)
        c2 = info_table.cell(0, 1)

        c1.text = f"Số MBL: {self.mbl_number or ''}"
        c2.text = f"HBL: {self.hbl_number or ''}"
        c1.paragraphs[0].runs[0].bold = True

        # Row 2: Vessel / Voyage
        c1 = info_table.cell(1, 0)
        c2 = info_table.cell(1, 1)
        c1.merge(c2)
        p_vessel = c1.paragraphs[0]
        p_vessel.add_run("Lô hàng kê khai dưới đây ở tàu: ")
        p_vessel.add_run(f"{self.vessel_name or ''}").bold = True
        p_vessel.add_run(f"\tChuyến: {self.voyage or ''}")
        p_vessel.add_run("\nVessel Name")

        # Row 3: From / To / Arrival
        c1 = info_table.cell(2, 0)
        c2 = info_table.cell(2, 1)
        c1.merge(c2)
        p_route = c1.paragraphs[0]
        p_route.add_run(f"Từ: {self.pol_id.name or ''}\t\tđến: {self.pod_id.name or ''}")

        eta_str = self.eta.strftime('%d/%m/%Y') if self.eta else "................"
        p_route.add_run(f"\t\tNgày đến: {eta_str}")
        p_route.add_run("\nFrom\t\t\t\tto\t\t\t\tArrival Date")
        p_route.paragraph_format.space_after = Pt(0)
        # 6. TABLE HÀNG HÓA
        # 5 Cột: Container/Seal | Số Kiện | Tên Hàng | Trọng Lượng | Kích Thước
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'

        # Header
        hdr_cells = table.rows[0].cells
        headers = [
            "SỐ CONTAINER;\nSỐ SEAL\nMarks and Nos; Container/Seal No.",
            "SỐ KIỆN\nNo. of Package",
            "KÝ MÃ HIỆU\nTÊN HÀNG HÓA\nDescription of Goods",
            "TRỌNG LƯỢNG (KGM)\nGross Weight",
            "KÍCH THƯỚC (M3)\nMeasurement"
        ]

        for i, h in enumerate(headers):
            cell = hdr_cells[i]
            cell.text = h
            # Bold & Center header
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.bold = True
                    r.font.size = Pt(10)

        # Data
        for line in self.container_line_ids:
            row_cells = table.add_row().cells
            # Col 1
            row_cells[0].text = f"{line.container_number or ''}\n{line.seal_number or ''}"
            row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Col 2
            row_cells[1].text = str(line.packages or '')
            row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Col 3
            row_cells[2].text = line.goods_description or ''

            # Col 4
            w_str = f"{line.gross_weight:,.2f}" if line.gross_weight else ""
            row_cells[3].text = w_str
            row_cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Col 5
            m_str = str(line.measurement) if line.measurement else ""
            row_cells[4].text = m_str
            row_cells[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 7. FOOTER NOTE & SIGNATURE
        p_note1 = doc.add_paragraph("LƯU Ý: Xin quý khách vui lòng đối chiếu chi tiết hàng khi nhận lệnh giao hàng.")
        p_note1.paragraph_format.space_before = Pt(12)
        p_note1.paragraph_format.space_after = Pt(0)

        p_note2 = doc.add_paragraph("Rất cảm ơn sự hợp tác và ủng hộ của Quý khách hàng.")
        p_note2.paragraph_format.space_after = Pt(12)
        # Ngày tháng ký (Canh phải)
        p_date = doc.add_paragraph()
        p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        today_str = f"................., ngày {fields.Date.today().day} tháng {fields.Date.today().month} năm {fields.Date.today().year}"
        p_date.add_run(today_str).bold = True

        # Bảng chữ ký và thông tin người nhận
        # 2 Cột: Trái (Ký nhận) - Phải (Thông tin người nhận)
        sign_table = doc.add_table(rows=1, cols=2)
        sign_table.autofit = False
        sign_table.columns[0].width = Cm(11)
        sign_table.columns[1].width = Cm(8)

        c_left = sign_table.cell(0, 0)
        c_right = sign_table.cell(0, 1)

        p_left = c_left.paragraphs[0]

        # 1. Tiêu đề ký nhận
        run_title = p_left.add_run("Ký nhận đủ bộ chứng từ\n")
        run_title.bold = True

        # 2. Dòng ngày ký của khách
        p_left.add_run("Ngày:.......................\n")

        # 3. Thông tin người nhận (Consignee Contact Info)
        contact_name = self.contact_name or "..................................."
        contact_phone = self.contact_phone or "......................."
        contact_tax = self.contact_tax_code or "........................"

        p_left.add_run(f"Họ và tên: {contact_name}\n")
        p_left.add_run(f"Số điện thoại: {contact_phone}\n")
        p_left.add_run(f"Mã số thuế: {contact_tax}")

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        return self._create_attachment_download(output.read(), f'Delivery_Order_{self.document_number}.docx', 'docx')

    def _create_attachment_download(self, data, filename, file_type):
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_type == 'xlsx' else \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': mimetype
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
