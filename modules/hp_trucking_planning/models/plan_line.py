from odoo import models, api, fields
from odoo.exceptions import UserError
import base64


class PlanLine(models.Model):
    _name = 'trucking_planning.plan.line'
    _description = 'Plan Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date asc'

    plan_id = fields.Many2one(
        comodel_name='trucking_planning.plan',
        string='Plan',
        required=True,
    )
    code = fields.Char(
        string='Job Number',
        required=True,
        tracking=True,
    )
    date = fields.Date(
        required=True,
        related='plan_id.date',
        readonly=True,
        string='Return Shipment Date',
        tracking=True,
    )
    plan_month = fields.Integer(
        string='Plan Month',
        compute='_compute_plan_month_year',
        store=True,
        readonly=True,
    )
    plan_year = fields.Integer(
        string='Plan Year',
        compute='_compute_plan_month_year',
        store=True,
        readonly=True,
    )
    status = fields.Selection([
            ('hpl_reject','HPL Reject'),
            ('client_cancel','Client Cancel'),
            ('checking','Checking'),
            ('transfer','Transfer'),
            ('rented','Rented')
        ],
        string='Status',
        required=True,
        tracking=True,
    )
    client_id = fields.Many2one(
        comodel_name='trucking_planning.client',
        required=True,
    )
    tax_number = fields.Char(
        related='client_id.tax_number',
        readonly=True,
        string='Tax number',
        store=True,
        tracking=True,
    )
    booking = fields.Char(
        string="Booking",
        required=True,
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
        ('dry','Dry'),
        ('cool','Cool'),
        ('ot','OT'),
        ('ft','FT')
    ], string="Container Type", required=True, tracking=True)

    container_size = fields.Selection([
        ('20','20'),
        ('40','40')
    ], string="Container Size", required=True, tracking=True)
    shipping_line_id = fields.Many2one(
        comodel_name='trucking_planning.shipping_line',
        required=True,
    )
    plan_type = fields.Selection([
        ('export','Export'),
        ('import','Import'),
    ], string="Plan Type", required=True, tracking=True)

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
        string = 'To Location',
        store=True,
        readonly=True,
        tracking=True,
    )
    container_pickup = fields.Many2one(
        comodel_name="trucking_planning.location",
        required=True,
    )
    goods_pickup_delivery = fields.Many2one(
        comodel_name="trucking_planning.location",
        required=True,
    )
    contact_phone = fields.Char(
        string="Contact Phone",
        related='goods_pickup_delivery.contact_phone',
    )
    container_delivery = fields.Many2one(
        comodel_name="trucking_planning.location",
        required=True,
    )
    truck_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        related='plan_id.vehicle_id',
        readonly=True,
        store=True,
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
        related='plan_id.vehicle_id.trailer_id',
        readonly=True,
        store=True,
    )
    is_rented = fields.Boolean(
        related='truck_id.is_rented',
        string="Is Rented",
        tracking=True,
    )
    contract_number = fields.Char(
        string="Contact Number",
        tracking=True,
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
    extra_charge = fields.Float(string="Extra Charge", tracking=True)
    extra_fuel = fields.Float(string="Extra Fuel", tracking=True)
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
        ('unique_booking','Unique(booking)','Booking number is unique!'),
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

    @api.depends('route_id', 'truck_id', 'weight_class','extra_fuel')
    def _compute_fuel_liters(self):
        for rec in self:
            if rec.route_id and rec.truck_id:
                fuel_rate = rec.truck_id.fuel_rate_mix
                if rec.weight_class == 'inferior_20':
                    fuel_rate = rec.truck_id.fuel_rate_inferior_20
                elif rec.weight_class == 'superior_20':
                    fuel_rate = rec.truck_id.fuel_rate_superior_20
                distance = rec.route_id.distance_km
                if rec.route_id.extra_fuel:
                    distance = rec.route_id.distance_km + 40
                rec.fuel_liters = distance * fuel_rate * 2 + rec.extra_fuel
            else:
                rec.fuel_liters = 0.0

    @api.depends('route_id','extra_charge')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.route_id.total_cost + rec.extra_charge
    


    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id and self.plan_id.vehicle_id and self._origin.plan_id != self.plan_id:
            self.driver_id = self.plan_id.vehicle_id.primary_driver_id

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
        
        # Create attachment
        filename = f"GiayVanTai_{self.driver_id.name if self.driver_id else 'Bùi Văn Thắng'}_{self.date.strftime('%d/%m/%Y') if self.date else '22/08/2025'}.docx"
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
        style.font.size = Pt(12)

        # Header Table
        header_table = doc.add_table(rows=1, cols=2)
        header_table.style = 'Table Grid'
        header_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        
        # Remove table borders
        for row in header_table.rows:
            for cell in row.cells:
                cell._tc.get_or_add_tcPr().append(parse_xml(r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(12)

        # Left cell - Company info
        header_table.cell(0, 0).text = ""
        company_para = header_table.cell(0, 0).add_paragraph()
        title_run = company_para.add_run("1. Thông tin về đơn vị kinh doanh")
        title_run.bold = True
        company_para.add_run("\nĐơn vị vận tải: CHI NHÁNH CÔNG TY CP TIẾP VẬN HP TẠI TP. HẢI PHÒNG")
        company_para.add_run("\nĐịa chỉ: Room 202A, Dau Khi Hotel, 441 Da Nang Street, Hai An, Hai Phong, Vietnam")
        company_para.add_run("\nTel: +84 225 3556133 Fax: + 84 225 3556132")

        # Right cell - Government heading
        header_table.cell(0, 1).text = ""
        gov_para = header_table.cell(0, 1).add_paragraph()
        gov_para.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
        gov_para.add_run("\nĐộc lập - Tự do - Hạnh phúc")
        gov_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()  # Spacer

        # Create table with 3 columns for title, info, and driver info
        info_table = doc.add_table(rows=2, cols=3)
        info_table.style = 'Table Grid'
        info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Remove table borders
        for row in info_table.rows:
            for cell in row.cells:
                cell._tc.get_or_add_tcPr().append(parse_xml(r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(12)

        # Merge first column across both rows
        info_table.cell(0, 0).merge(info_table.cell(1, 0))
        driver_cell = info_table.cell(0, 0)
        driver_cell.text = ""
        
        # Add empty paragraphs to push content to bottom
        for i in range(4):  # Add 8 empty paragraphs to push content down
            driver_cell.add_paragraph()
        
        # Add driver info at the bottom
        driver_para = driver_cell.add_paragraph()
        title_run = driver_para.add_run("2. Thông tin về người lái xe")
        title_run.bold = True
        driver_para.add_run("\nTên tài xế: ")
        bold_run = driver_para.add_run(f"{self.driver_id.name if self.driver_id else 'Bùi Văn Thắng'}")
        bold_run.bold = True
        driver_para.add_run("\nSố điện thoại liên hệ: ")
        bold_run = driver_para.add_run(f"{getattr(self.driver_id, 'phone', '0358636726')}")
        bold_run.bold = True

        # Merge 2nd and 3rd columns for the first row
        info_table.cell(0, 1).merge(info_table.cell(0, 2))
        title_cell = info_table.cell(0, 1)
        
        # Clear existing content and create paragraphs properly
        title_cell.text = ""
        
        # Add title paragraph
        title_para = title_cell.paragraphs[0]
        title_run = title_para.add_run("GIẤY VẬN TẢI")
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run.bold = True
        title_run.font.size = Pt(16)
        
        # Add subtitle paragraph
        subtitle_para = title_cell.add_paragraph()
        subtitle_run = subtitle_para.add_run("(Ban hành kèm theo Thông tư số: 63/2014/TT-BGTVT ngày 07 tháng 11 năm 2014 của Bộ trưởng Bộ giao thông vận tải)")
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Second row - Vehicle number and Document info
        vehicle_cell = info_table.cell(1, 1)
        vehicle_cell.text = ""
        vehicle_cell.add_paragraph()
        vehicle_cell.add_paragraph()
        vehicle_para = vehicle_cell.add_paragraph()
        vehicle_para.add_run("Số Xe: ")
        bold_run = vehicle_para.add_run(f"{self.truck_id.name if self.truck_id and self.truck_id.name else '80A0332348'}")
        bold_run.bold = True

        info_cell = info_table.cell(1, 2)
        info_cell.text = ""
        info_para = info_cell.add_paragraph()
        info_para.add_run("Số: ")
        bold_run = info_para.add_run(f"{self.code or '656564564645'}")
        bold_run.bold = True
        info_para.add_run("    ")
        info_para.add_run("\nNgày đóng/trả hàng: ")
        bold_run = info_para.add_run(f"{self.date.strftime('%d/%m/%Y') if self.date else '22/08/2025'}")
        bold_run.bold = True

        doc.add_paragraph()  # Spacer

        # Main Table
        main_table = doc.add_table(rows=4, cols=3)
        main_table.style = 'Table Grid'
        main_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        hdr_cells = main_table.rows[0].cells
        hdr_cells[0].text = ""
        hdr_cells[1].text = ""
        hdr_cells[2].text = ""
        
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
        detail_cells[0].text = ""
        
        # Add booking info
        para1 = detail_cells[0].add_paragraph()
        title_run = para1.add_run(f"Số booking HPL: {self.booking or '3233234323232'}")
        title_run.bold = True
        
        # Add client info with bold title
        para2 = detail_cells[0].add_paragraph()
        title_run = para2.add_run("3. Thông tin về người thuê vận tải")
        title_run.bold = True
        
        para2_content = detail_cells[0].add_paragraph()
        para2_content.add_run("Tên người thuê vận chuyển: ")
        bold_run = para2_content.add_run(f"{self.client_id.name or 'Samsung'}")
        bold_run.bold = True
        para2_content.add_run("\nĐịa chỉ: ")
        bold_run = para2_content.add_run(f"{getattr(self.client_id, 'address', 'Số nhà 14C, ngõ 69/14, phố Trung Liệt, Phường Trung Liệt, Quận Đống Đa, TP Hà Nội')}")
        bold_run.bold = True
        
        # Add contract info with bold title
        detail_cells[0].add_paragraph()
        para3 = detail_cells[0].add_paragraph()
        title_run = para3.add_run("4. Thông tin về hợp đồng vận tải")
        title_run.bold = True
        
        para3_content = detail_cells[0].add_paragraph()
        para3_content.add_run("Số hợp đồng: ")
        bold_run = para3_content.add_run(f"{self.contract_number or '75645435435435'}")
        bold_run.bold = True
        para3_content.add_run("\nSố bill/booking: ")
        bold_run = para3_content.add_run(f"{self.booking or '3233234323232'}")
        bold_run.bold = True
        para3_content.add_run("\nSố cont: ")
        bold_run = para3_content.add_run(f"{self.container_number or '4343433'}")
        bold_run.bold = True
        para3_content.add_run("\nSố seal: ")
        bold_run = para3_content.add_run(f"{self.seal_number or '3232532432'}")
        bold_run.bold = True
        para3_content.add_run("\nLoại cont: ")
        bold_run = para3_content.add_run(f"{dict(self._fields['container_type'].selection).get(self.container_type, 'Khô')}")
        bold_run.bold = True
        para3_content.add_run("\nKích thước: ")
        bold_run = para3_content.add_run(f"{self.container_size or '40'}")
        bold_run.bold = True
        
        # Add trip info with bold title
        detail_cells[0].add_paragraph()
        para4 = detail_cells[0].add_paragraph()
        title_run = para4.add_run("5. Thông tin về chuyến đi")
        title_run.bold = True
        
        para4_content = detail_cells[0].add_paragraph()
        para4_content.add_run("Tuyến vận chuyển: ")
        bold_run = para4_content.add_run(f"{self.route_id.name or 'Cảng Lạch Huyện - Cảng Lạch Huyện'}")
        bold_run.bold = True
        para4_content.add_run("\nĐiểm xếp hàng: ")
        bold_run = para4_content.add_run(f"{self.container_pickup.name or 'Cảng Lạch Huyện'}")
        bold_run.bold = True
        para4_content.add_run("\nĐiểm giao hàng: ")
        bold_run = para4_content.add_run(f"{self.container_delivery.name or 'Cảng Lạch Huyện'}")
        bold_run.bold = True
        para4_content.add_run("\nNơi trả vỏ: ")
        bold_run = para4_content.add_run(f"{self.container_pickup.name or 'Cảng Lạch Huyện'}")
        bold_run.bold = True
        para4_content.add_run("\nThời gian vận chuyển dự kiến:")
        para4_content.add_run("\nBắt đầu từ: ")
        bold_run = para4_content.add_run(f"{self.date.strftime('%d/%m/%Y') if self.date else '22/08/2025'}")
        bold_run.bold = True
        para4_content.add_run(" đến: ")
        bold_run = para4_content.add_run(f"{self.date.strftime('%d/%m/%Y') if self.date else '22/08/2025'}")
        bold_run.bold = True
        para4_content.add_run("\nTổng số km dự kiến: ")
        bold_run = para4_content.add_run("200.00")
        bold_run.bold = True
        para4_content.add_run("\nLiên hệ: ")
        bold_run = para4_content.add_run(f"{self.contact_phone or '0933423223'}")
        bold_run.bold = True
        
        # Add goods info with bold title
        detail_cells[0].add_paragraph()
        para5 = detail_cells[0].add_paragraph()
        title_run = para5.add_run("6. Thông tin về hàng hóa")
        title_run.bold = True
        
        para5_content = detail_cells[0].add_paragraph()
        para5_content.add_run("Tên hàng hóa: ")
        para5_content.add_run("\nKhối lượng hàng hóa (tấn): ")
        bold_run = para5_content.add_run("28.00")
        bold_run.bold = True
        para5_content.add_run("\nCắt máng: ")

        detail_cells[0].add_paragraph()
        para6 = detail_cells[0].add_paragraph()
        title_run = para6.add_run("7. Thông tin về rơ mooc, sơ mi ro mooc")
        title_run.bold = True
        
        para6_content = detail_cells[0].add_paragraph()
        para6_content.add_run("Biển số rơ mooc, sơmi rơmooc: ")
        bold_run = para6_content.add_run(f"{self.trailer_id.name or '15R13049'}")
        bold_run.bold = True

        # Hàng Về (Inbound - blank template)
        # Clear cell and add content properly
        detail_cells[1].text = ""
        
        # Add booking info
        para1_inbound = detail_cells[1].add_paragraph()
        title_run = para1_inbound.add_run(f"Số booking HPL: {self.booking or '3233234323232'}")
        title_run.bold = True
        
        # Add client info with bold title
        para2_inbound = detail_cells[1].add_paragraph()
        title_run = para2_inbound.add_run("3. Thông tin về người thuê vận tải")
        title_run.bold = True
        
        para2_inbound_content = detail_cells[1].add_paragraph()
        para2_inbound_content.add_run("""
Tên người thuê vận chuyển:
Địa chỉ:""")
        
        # Add contract info with bold title
        detail_cells[1].add_paragraph()
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
        detail_cells[1].add_paragraph()
        para4_inbound = detail_cells[1].add_paragraph()
        title_run = para4_inbound.add_run("5. Thông tin về chuyến đi")
        title_run.bold = True
        
        para4_inbound_content = detail_cells[1].add_paragraph()
        para4_inbound_content.add_run("Tuyến vận chuyển:")
        para4_inbound_content.add_run("\nĐiểm xếp hàng:")
        para4_inbound_content.add_run("\nĐiểm giao hàng:")
        para4_inbound_content.add_run("\nNơi trả vỏ:")
        para4_inbound_content.add_run("\nThời gian vận chuyển dự kiến:")
        para4_inbound_content.add_run("\nBắt đầu từ: đến:")
        para4_inbound_content.add_run("\nTổng số km dự kiến: ")
        bold_run = para4_inbound_content.add_run("0.00")
        bold_run.bold = True
        para4_inbound_content.add_run("\nLiên hệ:")
        
        # Add goods info with bold title
        detail_cells[1].add_paragraph()
        para5_inbound = detail_cells[1].add_paragraph()
        title_run = para5_inbound.add_run("6. Thông tin về hàng hóa")
        title_run.bold = True
        
        para5_content = detail_cells[1].add_paragraph()
        para5_content.add_run("Tên hàng hóa:")
        para5_content.add_run("\nKhối lượng hàng hóa (tấn): ")
        bold_run = para5_content.add_run("0.00")
        bold_run.bold = True
        para5_content.add_run("\nCắt máng:")

        detail_cells[1].add_paragraph()
        para6_inbound = detail_cells[1].add_paragraph()
        title_run = para6_inbound.add_run("7. Thông tin về rơ mooc, sơ mi ro mooc")
        title_run.bold = True
        
        para6_content = detail_cells[1].add_paragraph()
        para6_content.add_run("""
Biển số rơ mooc, sơmi rơmooc:""")

        # Cấp Phép (Right side)
        # Clear cell and add content properly
        detail_cells[2].text = ""
        
        # Add fuel info
        para1_permit = detail_cells[2].add_paragraph()
        title_run = para1_permit.add_run(f"Nhiên Liệu - (LÍT DIZEL)")
        title_run.bold = True

        detail_cells[2].add_paragraph()
        para1_permit_content = detail_cells[2].add_paragraph()
        para1_permit_content.add_run("Tồn trước (lít): ")
        bold_run = para1_permit_content.add_run("0")
        bold_run.bold = True
        para1_permit_content.add_run("\nĐược lĩnh (lít): ")
        bold_run = para1_permit_content.add_run("70")
        bold_run.bold = True
        para1_permit_content.add_run("\nTổng cộng (lít): ")
        bold_run = para1_permit_content.add_run(f"{self.fuel_liters or 5098.0}")
        bold_run.bold = True
        
        # Add cost info
        detail_cells[2].add_paragraph()
        para2_permit = detail_cells[2].add_paragraph()
        title_run = para2_permit.add_run(f"TIỀN CHI PHÍ - (ĐỒNG)")
        title_run.bold = True

        detail_cells[2].add_paragraph()
        para2_permit_content = detail_cells[2].add_paragraph()
        para2_permit_content.add_run("Vé cầu đường: ")
        bold_run = para2_permit_content.add_run("392,000")
        bold_run.bold = True
        para2_permit_content.add_run("\nChi phí khác: ")
        bold_run = para2_permit_content.add_run("0")
        bold_run.bold = True
        para2_permit_content.add_run("\nĐi đường: ")
        bold_run = para2_permit_content.add_run("400,000")
        bold_run.bold = True
        para2_permit_content.add_run("\nTổng Cộng: ")
        bold_run = para2_permit_content.add_run(f"{self.total_cost or 5650000:,.0f}")
        bold_run.bold = True
        
        # Add loading/unloading info
        detail_cells[2].add_paragraph()
        detail_cells[2].add_paragraph()
        detail_cells[2].add_paragraph()
        detail_cells[2].add_paragraph()
        para3_permit = detail_cells[2].add_paragraph()
        para3_permit.add_run("Nâng hàng/vỏ: ")
        bold_run = para3_permit.add_run("0")
        bold_run.bold = True
        para3_permit.add_run("\nHạ vỏ/hàng: ")
        bold_run = para3_permit.add_run("0")
        bold_run.bold = True
        para3_permit.add_run("\nTổng cộng: ")
        bold_run = para3_permit.add_run("0")
        bold_run.bold = True
        para3_permit.add_run("\nTổng Tiền: ")
        bold_run = para3_permit.add_run(f"{self.total_cost or 5650000:,.0f}")
        bold_run.bold = True

        # Merge cells in main_table for the loader section
        main_table.cell(2, 0).merge(main_table.cell(2, 1)).merge(main_table.cell(2, 2))
        title_cell = main_table.cell(2, 0)
        para_loader = title_cell.add_paragraph()
        title_run = para_loader.add_run("8. Phần dành cho người xếp, dỡ hàng hóa lên, xuống xe ghi")
        title_run.bold = True

        loader_cells = main_table.rows[3].cells
        # Clear cells and add content properly
        loader_cells[0].text = ""
        loader_cells[1].text = ""
        
        # Loading info (left cell)
        para1_loader = loader_cells[0].add_paragraph()
        title_run = para1_loader.add_run("Thông tin về xếp hàng lên xe")
        title_run.bold = True
        
        para2_loader = loader_cells[0].add_paragraph()
        para2_loader.add_run("Xếp lần 1: Địa điểm")
        para2_loader.add_run("\nKhối lượng hàng:     ")
        bold_run = para2_loader.add_run("(tấn) thời gian:")
        bold_run.bold = True
        para2_loader.add_run("\nXác nhận của người xếp hàng:")
        loader_cells[0].add_paragraph()
        loader_cells[0].add_paragraph()

        para3_loader = loader_cells[0].add_paragraph()
        para3_loader.add_run("Xếp lần 2 Địa điểm")
        para3_loader.add_run("\nKhối lượng hàng:     ")
        bold_run = para3_loader.add_run("(tấn) thời gian:")
        bold_run.bold = True
        para3_loader.add_run("\nXác nhận của người xếp hàng:")
        loader_cells[0].add_paragraph()
        
        # Unloading info (right cell)
        para1_unloader = loader_cells[1].add_paragraph()
        title_run = para1_unloader.add_run("Thông tin về dỡ hàng xuống xe")
        title_run.bold = True
        loader_cells[1].add_paragraph()
        para2_unloader = loader_cells[1].add_paragraph()
        para2_unloader.add_run("Dỡ lần 1: Địa điểm")
        para2_unloader.add_run("\nKhối lượng hàng:     ")
        bold_run = para2_unloader.add_run("(tấn) thời gian:")
        bold_run.bold = True
        para2_unloader.add_run("\nXác nhận của người dỡ hàng:")
        loader_cells[1].add_paragraph()
        loader_cells[1].add_paragraph()
        para3_unloader = loader_cells[1].add_paragraph()
        para3_unloader.add_run("Dỡ lần 2 Địa điểm")
        para3_unloader.add_run("\nKhối lượng hàng:     ")
        bold_run = para3_unloader.add_run("(tấn) thời gian:")
        bold_run.bold = True
        para3_unloader.add_run("\nXác nhận của người dỡ hàng:")

        doc.add_paragraph()  # Spacer

        # Signature table
        sig_table = doc.add_table(rows=1, cols=3)
        sig_table.style = 'Table Grid'
        sig_cells = sig_table.rows[0].cells
        
        # Clear cells and add bold titles
        sig_cells[0].text = ""
        sig_cells[1].text = ""
        sig_cells[2].text = ""
        
        # First cell - NHÂN VIÊN LÀM LỆNH
        sig_para1 = sig_cells[0].add_paragraph()
        title_run = sig_para1.add_run("NHÂN VIÊN LÀM LỆNH")
        title_run.bold = True
        sig_cells[0].add_paragraph()
        sig_cells[0].add_paragraph()
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

    def _compute_location_info(self):
        for trip in self:
            contact_info = f"({trip.contact_phone})" if trip.contact_phone else ""
            trip.location_info = f"{trip.container_pickup.name},{trip.goods_pickup_delivery.name} {contact_info},{trip.container_delivery.name}"

    def _compute_driver_info(self):
        for trip in self:
            trip.driver_info = f"{trip.driver_id.name},{trip.truck_id.name}"