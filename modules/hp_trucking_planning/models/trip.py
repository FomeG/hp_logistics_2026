from odoo import models, api, fields
from odoo.exceptions import UserError
import base64
import math



class Trip(models.Model):
    _name = 'trucking_planning.trip'
    _description = 'Trip'
    _inherit = ['unique.code.mixin','mail.thread', 'mail.activity.mixin']

    plan_line_id = fields.Many2one(
        comodel_name='trucking_planning.plan.line',
        string='Plan',
        required=True,
    )
    code = fields.Char(
        string='Job Number',
        tracking=True,
    )
    status = fields.Selection([
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('checking', 'Checking'),
        ('done', 'Done'),
    ],
        default='checking',
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
    container_type = fields.Selection([
        ('dry', 'Dry'),
        ('cool', 'Cool'),
        ('ot', 'OT'),
        ('ft', 'FT')
    ], string="Container Type", required=True, tracking=True)

    container_size = fields.Selection([
        ('20', '20'),
        ('40', '40')
    ], string="Container Size", required=True, tracking=True)
    shipping_line_id = fields.Many2one(
        comodel_name='trucking_planning.shipping_line',
        required=True,
    )
    plan_type = fields.Selection([
        ('export', 'Export'),
        ('import', 'Import'),
    ], string="Plan Type", required=True, tracking=True)

    truck_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        index=True,
    )
    driver_id = fields.Many2one(
        comodel_name="trucking_planning.driver",
        related='truck_id.primary_driver_id',
        readonly=True,
        index=True,
    )
    trailer_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain=[('type', '=', 'trailer')],
        related='truck_id.trailer_id',
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
        string="Goods Name",
    )
    goods_weight = fields.Float(
        string="Goods Weight",
    )
    goods_cut_off = fields.Datetime(
        string="Cut Off",
    )

    route_info = fields.Text(
        compute='_compute_route_info',
        store=False,
    )
    container_info = fields.Char(
        compute='_compute_container_info',
        store=False,
    )
    location_info = fields.Text(
        compute='_compute_location_info',
        store=False,
    )
    driver_info = fields.Text(
        compute='_compute_driver_info',
        store=False,
    )

    _sql_constraints = [
        ('unique_booking', 'Unique(booking)', 'Booking number is unique!'),
    ]

    @api.depends('plan_id.date')
    def _compute_plan_month_year(self):
        for record in self:
            if record.plan_id.date:
                record.plan_month = record.plan_id.date.month
                record.plan_year = record.plan_id.date.year
            else:
                record.plan_month = False
                record.plan_year = False

    @api.depends('plan_type', 'route_id')
    def _compute_actual_locations(self):
        for rec in self:
            if rec.route_id:
                if rec.plan_type == 'export':
                    rec.actual_source_location_id = rec.route_id.from_location_id
                    rec.actual_destination_location_id = rec.route_id.to_location_id
                else:  # import
                    rec.actual_source_location_id = rec.route_id.to_location_id
                    rec.actual_destination_location_id = rec.route_id.from_location_id
            else:
                rec.actual_source_location_id = False
                rec.actual_destination_location_id = False

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

    def action_export_trip_docx(self):
        """Export trip data to DOCX format matching the transport document"""
        try:
            from docx import Document
            from docx.shared import Inches, Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.table import WD_TABLE_ALIGNMENT
        except ImportError:
            raise UserError("python-docx library is required. Please install it using: pip install python-docx")

        # Generate the DOCX file
        doc = self._generate_trip_docx()

        # Save document to memory
        import io
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)

        if not self.driver_id:
            raise UserError("No driver id specified")
        # Create attachment
        filename = f"GiayVanTai_{self.driver_id.name if self.driver_id else 'N/A'}_{self.date.strftime('%d/%m/%Y') if self.date else fields.Date.today().strftime('%d/%m/%Y')}.docx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(doc_io.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _generate_trip_docx(self):
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

        # doc.add_paragraph()  # Spacer

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
        bold_run = driver_para.add_run(f"{self.driver_id.name if self.driver_id else 'Bùi Văn Thắng'}")
        bold_run.bold = True
        driver_para.add_run("\nSố điện thoại liên hệ: ")
        bold_run = driver_para.add_run(f"{getattr(self.driver_id, 'phone_number', 'N/A')}")
        bold_run.bold = True

        # Merge 2nd and 3rd columns for the first row
        info_table.cell(0, 1).merge(info_table.cell(0, 2))
        title_cell = info_table.cell(0, 1)

        # Clear existing content and create paragraphs properly
        # Clear all paragraphs first
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
        bold_run = vehicle_para.add_run(f"{self.truck_id.name if self.truck_id and self.truck_id.name else ' '}")
        bold_run.bold = True
        vehicle_para.add_run("    ")
        vehicle_para.add_run("\nSố Rơ mooc: ")
        bold_run = vehicle_para.add_run(
            f"{self.truck_id.trailer_id.name if self.truck_id and self.truck_id.trailer_id else ' '}")
        bold_run.bold = True

        info_cell = info_table.cell(1, 2)
        # Clear all paragraphs first
        for paragraph in info_cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        info_para = info_cell.add_paragraph()
        info_para.add_run("Số: ")
        bold_run = info_para.add_run(f"{self.code or ' '}")
        bold_run.bold = True
        info_para.add_run("    ")
        info_para.add_run("\nNgày đóng/trả hàng: ")
        bold_run = info_para.add_run(f"{self.date.strftime('%d/%m/%Y') if self.date else ' '}")
        bold_run.bold = True

        # doc.add_paragraph()  # Spacer

        # Main Table
        main_table = doc.add_table(rows=2, cols=3)
        main_table.style = 'Table Grid'
        main_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        hdr_cells = main_table.rows[0].cells
        # Clear all paragraphs first
        for paragraph in hdr_cells[0].paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        for paragraph in hdr_cells[1].paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        for paragraph in hdr_cells[2].paragraphs:
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
        # Hàng Đi (Outbound)
        # Clear cell and add content properly
        # Clear all paragraphs first
        for paragraph in detail_cells[0].paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        # Add booking info
        para1 = detail_cells[0].add_paragraph()
        title_run = para1.add_run(f"Số booking HPL: {self.booking or 'N/A'}")
        title_run.bold = True
        title_run.underline = True
        # Add top padding to the inbound cell
        detail_cells[0]._tc.get_or_add_tcPr().append(parse_xml(
            r'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="20" w:type="dxa"/></w:tcMar>'))

        # Add client info with bold title
        para2 = detail_cells[0].add_paragraph()
        title_run = para2.add_run("3. Thông tin về người thuê vận tải")
        title_run.bold = True

        para2_content = detail_cells[0].add_paragraph()
        para2_content.add_run("Tên người thuê vận chuyển: ")
        bold_run = para2_content.add_run(f"{self.client_id.name or 'N/A'}")
        bold_run.bold = True
        para2_content.add_run("\nĐịa chỉ: ")
        bold_run = para2_content.add_run(f"{getattr(self.client_id, 'address', '')}")
        bold_run.bold = True

        # Add contract info with bold title
        # detail_cells[0].add_paragraph()
        para3 = detail_cells[0].add_paragraph()
        title_run = para3.add_run("4. Thông tin về hợp đồng vận tải")
        title_run.bold = True

        para3_content = detail_cells[0].add_paragraph()
        para3_content.add_run("Số hợp đồng: ")
        bold_run = para3_content.add_run("")
        bold_run.bold = True
        para3_content.add_run("\nSố bill/booking: ")
        bold_run = para3_content.add_run(f"{self.booking or ' '}")
        bold_run.bold = True
        para3_content.add_run("\nSố cont: ")
        bold_run = para3_content.add_run(f"{self.container_number or ' '}")
        bold_run.bold = True
        para3_content.add_run("\nSố seal: ")
        bold_run = para3_content.add_run(f"{self.seal_number or ' '}")
        bold_run.bold = True
        para3_content.add_run("\nLoại cont: ")
        bold_run = para3_content.add_run(
            f"{dict(self._fields['container_type'].selection).get(self.container_type, '')}")
        bold_run.bold = True
        para3_content.add_run("\nKích thước: ")
        bold_run = para3_content.add_run(f"{self.container_size or '40'}")
        bold_run.bold = True

        # Add trip info with bold title
        # detail_cells[0].add_paragraph()
        para4 = detail_cells[0].add_paragraph()
        title_run = para4.add_run("5. Thông tin về chuyến đi")
        title_run.bold = True

        para4_content = detail_cells[0].add_paragraph()
        para4_content.add_run("Tuyến vận chuyển: ")
        bold_run = para4_content.add_run(f"{self.route_id.name or ' '}")
        bold_run.bold = True
        para4_content.add_run("\nĐiểm xếp hàng: ")
        bold_run = para4_content.add_run(f"{self.container_pickup.name or ' '}")
        bold_run.bold = True
        para4_content.add_run("\nĐiểm giao hàng: ")
        bold_run = para4_content.add_run(f"{self.container_delivery.name or ' '}")
        bold_run.bold = True
        para4_content.add_run("\nNơi trả vỏ: ")
        bold_run = para4_content.add_run(f"{self.container_pickup.name or ' '}")
        bold_run.bold = True
        para4_content.add_run("\nThời gian vận chuyển dự kiến:")
        para4_content.add_run("\nBắt đầu từ: ")
        bold_run = para4_content.add_run(" ")
        bold_run.bold = True
        para4_content.add_run("\nđến: ")
        bold_run = para4_content.add_run(" ")
        bold_run.bold = True
        para4_content.add_run("\nTổng số km dự kiến: ")
        bold_run = para4_content.add_run(f"{self.route_id.distance_km}")
        bold_run.bold = True
        para4_content.add_run("\nLiên hệ: ")
        bold_run = para4_content.add_run(f"{self.goods_pickup_delivery.contact_phone or ' '}")
        bold_run.bold = True

        # Add goods info with bold title
        # detail_cells[0].add_paragraph()
        para5 = detail_cells[0].add_paragraph()
        title_run = para5.add_run("6. Thông tin về hàng hóa")
        title_run.bold = True

        para5_content = detail_cells[0].add_paragraph()
        para5_content.add_run("Tên hàng hóa: ")
        bold_run = para5_content.add_run({self.goods_weight or ' '})
        bold_run.bold = True
        para5_content.add_run("\nKhối lượng hàng hóa (tấn): ")
        bold_run = para5_content.add_run({self.goods_weight or ' '})
        bold_run.bold = True
        para5_content.add_run("\nCắt máng (Cut off): ")
        cut_off_str = self.goods_cut_off.strftime('%d/%m/%Y %H:%M') if self.goods_cut_off else ' '
        bold_run = para5_content.add_run(f"{cut_off_str}")
        bold_run.bold = True

        # detail_cells[0].add_paragraph()
        # para6 = detail_cells[0].add_paragraph()
        # title_run = para6.add_run("7. Thông tin về rơ mooc, sơ mi ro mooc")
        # title_run.bold = True
        #
        # para6_content = detail_cells[0].add_paragraph()
        # para6_content.add_run("Biển số rơ mooc, sơmi rơmooc: ")
        # bold_run = para6_content.add_run(f"{self.trailer_id.name or '15R13049'}")
        # bold_run.bold = True

        # Hàng Về (Inbound - blank template)
        # Clear cell and add content properly
        # Clear all paragraphs first
        for paragraph in detail_cells[1].paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        # Add booking info
        para1_inbound = detail_cells[1].add_paragraph()
        title_run = para1_inbound.add_run(f"Số booking HPL: ")
        title_run.bold = True
        title_run.underline = True
        # Add top padding to the inbound cell
        detail_cells[1]._tc.get_or_add_tcPr().append(parse_xml(
            r'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="20" w:type="dxa"/></w:tcMar>'))

        # Add client info with bold title
        para2_inbound = detail_cells[1].add_paragraph()
        title_run = para2_inbound.add_run("3. Thông tin về người thuê vận tải")
        title_run.bold = True
        para2_inbound_content = detail_cells[1].add_paragraph()
        para2_inbound_content.add_run("Tên người thuê vận chuyển:\nĐịa chỉ:")
        # Add contract info with bold title
        # detail_cells[1].add_paragraph()
        para3_inbound = detail_cells[1].add_paragraph()
        title_run = para3_inbound.add_run("4. Thông tin về hợp đồng vận tải")
        title_run.bold = True

        para3_inbound_content = detail_cells[1].add_paragraph()
        para3_inbound_content.add_run("Số hợp đồng:")
        para3_inbound_content.add_run("\nSố bill/booking:")
        para3_inbound_content.add_run("\nSố cont:")
        para3_inbound_content.add_run("\nSố seal:")
        para3_inbound_content.add_run("\nLoại cont:")
        para3_inbound_content.add_run("\nKích thước:")

        # Add trip info with bold title
        # detail_cells[1].add_paragraph()
        para4_inbound = detail_cells[1].add_paragraph()
        title_run = para4_inbound.add_run("5. Thông tin về chuyến đi")
        title_run.bold = True

        para4_inbound_content = detail_cells[1].add_paragraph()
        para4_inbound_content.add_run("Tuyến vận chuyển:")
        para4_inbound_content.add_run("\nĐiểm xếp hàng:")
        para4_inbound_content.add_run("\nĐiểm giao hàng:")
        para4_inbound_content.add_run("\nNơi trả vỏ:")
        para4_inbound_content.add_run("\nThời gian vận chuyển dự kiến:")
        para4_inbound_content.add_run("\nBắt đầu từ: ")
        para4_inbound_content.add_run("\nđến: ")
        para4_inbound_content.add_run("\nTổng số km dự kiến: ")
        bold_run = para4_inbound_content.add_run("0.00")
        bold_run.bold = True
        para4_inbound_content.add_run("\nLiên hệ:")

        # Add goods info with bold title
        # detail_cells[1].add_paragraph()
        para5_inbound = detail_cells[1].add_paragraph()
        title_run = para5_inbound.add_run("6. Thông tin về hàng hóa")
        title_run.bold = True

        para5_content = detail_cells[1].add_paragraph()
        para5_content.add_run("Tên hàng hóa:")
        para5_content.add_run("\nKhối lượng hàng hóa (tấn): ")
        para5_content.add_run("\nCắt máng(Cut off):")

        # detail_cells[1].add_paragraph()
        para6_inbound = detail_cells[1].add_paragraph()
        #         title_run = para6_inbound.add_run("7. Thông tin về rơ mooc, sơ mi ro mooc")
        #         title_run.bold = True
        #
        #         para6_content = detail_cells[1].add_paragraph()
        #         para6_content.add_run("""
        # Biển số rơ mooc, sơmi rơmooc:""")

        # Cấp Phép (Right side)
        # Clear cell and add content properly
        # Clear all paragraphs first
        for paragraph in detail_cells[2].paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

        # Add fuel info
        para1_permit = detail_cells[2].add_paragraph()
        title_run = para1_permit.add_run(f"Nhiên Liệu - (LÍT DIZEL)")
        title_run.bold = True

        detail_cells[2].add_paragraph()
        para1_permit_content = detail_cells[2].add_paragraph()
        para1_permit_content.add_run("Tồn trước (lít): ")
        bold_run = para1_permit_content.add_run(" ")
        bold_run.bold = True
        para1_permit_content.add_run("\nĐược lĩnh (lít): ")
        bold_run = para1_permit_content.add_run(f"{self.fuel_liters or ''}")
        bold_run.bold = True
        para1_permit_content.add_run("\nTổng cộng (lít): ")
        bold_run = para1_permit_content.add_run(" ")
        bold_run.bold = True

        # Add cost info
        detail_cells[2].add_paragraph()
        detail_cells[2].add_paragraph()
        para2_permit = detail_cells[2].add_paragraph()
        title_run = para2_permit.add_run(f"TIỀN CHI PHÍ - (ĐỒNG)")
        title_run.bold = True
        para2_permit_content = detail_cells[2].add_paragraph()
        para2_permit_content.add_run("Vé cầu đường: ")
        bold_run = para2_permit_content.add_run(f"{self.route_id.road_fee or ''}")
        bold_run.bold = True
        para2_permit_content.add_run("\nChi phí khác: ")
        bold_run = para2_permit_content.add_run(f"{self.extra_charge or ''}")
        bold_run.bold = True
        para2_permit_content.add_run("\nĐi đường: ")
        bold_run = para2_permit_content.add_run("")
        bold_run.bold = True
        para2_permit_content.add_run("\nTổng Cộng: ")
        bold_run = para2_permit_content.add_run("")
        bold_run.bold = True

        # Add loading/unloading info
        detail_cells[2].add_paragraph()
        detail_cells[2].add_paragraph()
        detail_cells[2].add_paragraph()
        detail_cells[2].add_paragraph()
        para3_permit = detail_cells[2].add_paragraph()
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
        bold_run = para3_permit.add_run(" ")
        bold_run.bold = True

        # Merge cells in main_table for the loader section
        # main_table.cell(2, 0).merge(main_table.cell(2, 1)).merge(main_table.cell(2, 2))
        # title_cell = main_table.cell(2, 0)
        # # Clear all paragraphs first
        # for paragraph in title_cell.paragraphs:
        #     p = paragraph._element
        #     p.getparent().remove(p)
        # # Add top padding to the cell
        # title_cell._tc.get_or_add_tcPr().append(parse_xml(r'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="20" w:type="dxa"/></w:tcMar>'))
        # para_loader = title_cell.add_paragraph()
        # title_run = para_loader.add_run("8. Phần dành cho người xếp, dỡ hàng hóa lên, xuống xe ghi")
        # title_run.bold = True
        # # Add top padding to the cell (not the paragraph)
        # title_cell._tc.get_or_add_tcPr().append(parse_xml(r'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="20" w:type="dxa"/></w:tcMar>'))
        #
        #
        # loader_cells = main_table.rows[3].cells
        # # Clear cells and add content properly
        # # Clear all paragraphs first
        # for paragraph in loader_cells[0].paragraphs:
        #     p = paragraph._element
        #     p.getparent().remove(p)
        # for paragraph in loader_cells[1].paragraphs:
        #     p = paragraph._element
        #     p.getparent().remove(p)
        #
        # # Loading info (left cell)
        # para1_loader = loader_cells[0].add_paragraph()
        # title_run = para1_loader.add_run("Thông tin về xếp hàng lên xe")
        # title_run.bold = True
        #
        # para2_loader = loader_cells[0].add_paragraph()
        # para2_loader.add_run("Xếp lần 1: Địa điểm")
        # para2_loader.add_run("\nKhối lượng hàng:     ")
        # bold_run = para2_loader.add_run("(tấn) thời gian:")
        # bold_run.bold = True
        # para2_loader.add_run("\nXác nhận của người xếp hàng:")
        # loader_cells[0].add_paragraph()
        # loader_cells[0].add_paragraph()
        #
        # para3_loader = loader_cells[0].add_paragraph()
        # para3_loader.add_run("Xếp lần 2 Địa điểm")
        # para3_loader.add_run("\nKhối lượng hàng:     ")
        # bold_run = para3_loader.add_run("(tấn) thời gian:")
        # bold_run.bold = True
        # para3_loader.add_run("\nXác nhận của người xếp hàng:")
        # loader_cells[0].add_paragraph()
        #
        # # Unloading info (right cell)
        # para1_unloader = loader_cells[1].add_paragraph()
        # title_run = para1_unloader.add_run("Thông tin về dỡ hàng xuống xe")
        # title_run.bold = True
        # # loader_cells[1].add_paragraph()
        # para2_unloader = loader_cells[1].add_paragraph()
        # para2_unloader.add_run("Dỡ lần 1: Địa điểm")
        # para2_unloader.add_run("\nKhối lượng hàng:     ")
        # bold_run = para2_unloader.add_run("(tấn) thời gian:")
        # bold_run.bold = True
        # para2_unloader.add_run("\nXác nhận của người dỡ hàng:")
        # loader_cells[1].add_paragraph()
        # loader_cells[1].add_paragraph()
        # para3_unloader = loader_cells[1].add_paragraph()
        # para3_unloader.add_run("Dỡ lần 2 Địa điểm")
        # para3_unloader.add_run("\nKhối lượng hàng:     ")
        # bold_run = para3_unloader.add_run("(tấn) thời gian:")
        # bold_run.bold = True
        # para3_unloader.add_run("\nXác nhận của người dỡ hàng:")

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
        # Clear all paragraphs first
        for paragraph in sig_cells[0].paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        for paragraph in sig_cells[1].paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        for paragraph in sig_cells[2].paragraphs:
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

        return doc

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
