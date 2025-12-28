from odoo import models, api, fields
from odoo.exceptions import UserError
import base64
import io
from datetime import datetime

class HpDocumentService(models.AbstractModel):
    _name = 'hp.document.service'
    _description = 'Document Service Library'

    # Excel Methods
    def generate_excel(self, data, filename_prefix="export"):
        """Phương thức chính để generate Excel file."""
        raise NotImplementedError("Subclass must implement generate_excel()")

    def _get_excel_workbook(self):
        """Tạo workbook mới"""
        try:
            import xlsxwriter
        except ImportError:
            raise UserError("xlsxwriter library is required. Please install it using: pip install xlsxwriter")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        return workbook, output

    def _define_excel_formats(self, workbook):
        """Define các format styles cho Excel."""
        formats = {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#90EE90',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            }),
            'cell': workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            }),
            'date': workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'num_format': 'dd/mm/yyyy hh:mm'
            }),
            'center': workbook.add_format({
                'align': 'center',
                'valign': 'vcenter'
            }),
            'center_bold': workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'bold': True
            }),
            'italic_center': workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'italic': True
            }),
        }
        return formats

    def _write_excel_header(self, worksheet, headers, formats, row=0):
        """Viết header row cho Excel"""
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, formats['header'])

    def _write_excel_data_row(self, worksheet, row_data, formats, row_index, date_columns=None):
        """Viết một data row"""
        date_columns = date_columns or []
        for col, value in enumerate(row_data):
            if col in date_columns:
                worksheet.write(row_index, col, value, formats['date'])
            else:
                worksheet.write(row_index, col, value, formats['cell'])

    def _write_company_info_excel(self, worksheet, row_start=0, col_start=2):
        """Viết thông tin công ty vào Excel - Common for all modules"""
        company_info = [
            "CHI NHÁNH CÔNG TY CP TIẾP VẬN HP TẠI TP.HẢI PHÒNG",
            "Room 202A, Dau Khi Hotel, 441 Da Nang Street, Hai An, Hai Phong, Vietnam",
            "Tel: + 84 225 3556133 Fax: + 84 225 3556132",
            "Email: cs@hplogistics.com.vn",
            "Website: www.hplogistics.com.vn"
        ]
        for i, info in enumerate(company_info):
            worksheet.write(row_start + i, col_start, info)

    def _write_signature_section_excel(self, worksheet, workbook, last_data_row,
                                       signature_configs=None):
        """
        Viết phần signature vào Excel - Flexible để cs và trucking custom
        signature_configs: dict với format:
        {
            'signatures': [
                {'title': 'Người lập phiếu', 'name': 'Lê Quý Hùng', 'cols': (0, 1)},
                {'title': 'Kế toán trưởng', 'name': '', 'cols': (19, 19)},
                {'title': 'Giám đốc', 'name': 'Nguyễn Văn Bân', 'cols': (38, 38), 'show_date': True}
            ]
        }
        """
        center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        center_bold_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})
        italic_center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'italic': True})
        merged_border = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 0})

        if not signature_configs:
            # Default trucking style
            signature_configs = {
                'signatures': [
                    {'title': 'Người lập phiếu', 'subtitle': '(Ký, họ tên)',
                     'name': 'Lê Quý Hùng', 'cols': (0, 1)},
                    {'title': 'Kế toán trưởng', 'subtitle': '(Ký, họ tên)',
                     'name': '', 'cols': (19, 19)},
                    {'title': 'Giám đốc', 'subtitle': '(Đóng dấu, ký tên)',
                     'name': 'Nguyễn Văn Bân', 'cols': (38, 38), 'show_date': True}
                ]
            }

        for sig in signature_configs['signatures']:
            col_start, col_end = sig['cols']

            # Show date if needed
            if sig.get('show_date'):
                worksheet.write(last_data_row + 6, col_start,
                                'Ngày …..  tháng …..  năm 201….', center_format)

            # Title
            if col_start == col_end:
                worksheet.write(last_data_row + 7, col_start, sig['title'], center_bold_format)
            else:
                worksheet.merge_range(last_data_row + 7, col_start, last_data_row + 7, col_end,
                                      sig['title'], merged_border)

            # Subtitle
            if sig.get('subtitle'):
                if col_start == col_end:
                    worksheet.write(last_data_row + 8, col_start, sig['subtitle'], italic_center_format)
                else:
                    worksheet.merge_range(last_data_row + 8, col_start, last_data_row + 8, col_end,
                                          sig['subtitle'], italic_center_format)

            # Name
            if sig.get('name'):
                if col_start == col_end:
                    worksheet.write(last_data_row + 12, col_start, sig['name'], center_bold_format)
                else:
                    worksheet.merge_range(last_data_row + 12, col_start, last_data_row + 12, col_end,
                                          sig['name'], center_bold_format)

    def _finalize_excel(self, workbook, output, filename):
        """Close workbook và tạo attachment"""
        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    # DOCX Methods
    def generate_docx(self, data, filename_prefix="document"):
        """Phương thức để generate DOCX file."""
        raise NotImplementedError("Subclass must implement generate_docx()")

    def _get_docx_document(self):
        """Khởi tạo một Document mới"""
        try:
            from docx import Document
            from docx.shared import Inches, Pt
        except ImportError:
            raise UserError("python-docx library is required. Please install: pip install python-docx")

        doc = Document()

        # Set margins
        for section in doc.sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)

        # Set default font
        style = doc.styles['Normal']
        style.font.name = 'Tahoma'
        style.font.size = Pt(9.5)

        return doc

    def _add_docx_company_header(self, doc, header_config=None):
        """
        Thêm header công ty vào document - Common pattern
        header_config: dict để customize, ví dụ:
        {
            'style': 'trucking' hoặc 'cs',
            'show_logo': True,
            'company_info': {...}
        }
        """
        from docx.shared import Pt, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        if not header_config:
            header_config = {'style': 'trucking', 'show_logo': True}

        # Header Table
        header_table = doc.add_table(rows=1, cols=2)
        header_table.style = 'Table Grid'
        header_table.alignment = WD_TABLE_ALIGNMENT.LEFT

        # Remove table borders
        self._remove_table_borders(header_table)

        # Left cell - Company info
        company_cell = header_table.cell(0, 0)
        self._clear_cell_paragraphs(company_cell)

        if header_config['style'] == 'trucking':
            self._add_trucking_company_info(company_cell)
        elif header_config['style'] == 'cs':
            self._add_cs_company_info(company_cell, header_config.get('show_logo', True))

        # Right cell - Government heading (for trucking style)
        if header_config['style'] == 'trucking':
            gov_cell = header_table.cell(0, 1)
            self._clear_cell_paragraphs(gov_cell)

            gov_para = gov_cell.add_paragraph()
            gov_para.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
            gov_para.add_run("\nĐộc lập - Tự do - Hạnh phúc")
            gov_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_trucking_company_info(self, cell):
        """Thêm thông tin công ty theo style trucking"""
        company_para = cell.add_paragraph()
        title_run = company_para.add_run("1. Thông tin về đơn vị kinh doanh")
        title_run.bold = True
        company_para.add_run("\nĐơn vị vận tải: CHI NHÁNH CÔNG TY CP TIẾP VẬN HP TẠI TP. HẢI PHÒNG")
        company_para.add_run("\nĐịa chỉ: Room 202A, Dau Khi Hotel, 441 Da Nang Street, Hai An, Hai Phong, Vietnam")
        company_para.add_run("\nTel: +84 225 3556133 Fax: + 84 225 3556132")

    def _add_cs_company_info(self, cell, show_logo=True):
        """Thêm thông tin công ty theo style CS"""
        from docx.shared import Cm

        p_logo = cell.paragraphs[0]
        if show_logo and self.env.company.logo:
            image_data = io.BytesIO(base64.b64decode(self.env.company.logo))
            p_logo.add_run().add_picture(image_data, width=Cm(3.5))

    def _add_docx_signature_section(self, doc, signature_config=None):
        """
        Thêm phần signature - Common pattern
        signature_config: dict để customize
        {
            'signatures': [
                {'title': 'NHÂN VIÊN LÀM LỆNH', 'name': ''},
                {'title': 'LÁI XE NHẬN LỆNH', 'name': ''},
                {'title': 'T/L GIÁM ĐỐC CÔNG TY', 'name': ''}
            ]
        }
        """
        from docx.shared import Pt
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml

        if not signature_config:
            # Default trucking style
            signature_config = {
                'signatures': [
                    {'title': 'NHÂN VIÊN LÀM LỆNH'},
                    {'title': 'LÁI XE NHẬN LỆNH'},
                    {'title': 'T/L GIÁM ĐỐC CÔNG TY'}
                ]
            }

        num_sigs = len(signature_config['signatures'])
        sig_table = doc.add_table(rows=1, cols=num_sigs)
        sig_table.style = 'Table Grid'
        sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Remove borders and add top padding
        for row in sig_table.rows:
            for cell in row.cells:
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    r'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="20" w:type="dxa"/></w:tcMar>'))
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9.5)

        sig_cells = sig_table.rows[0].cells

        # Add signatures
        for i, sig in enumerate(signature_config['signatures']):
            self._clear_cell_paragraphs(sig_cells[i])

            sig_para = sig_cells[i].add_paragraph()
            title_run = sig_para.add_run(sig['title'])
            title_run.bold = True

            # Add spacing
            for _ in range(3):
                sig_cells[i].add_paragraph()

            # Add name if provided
            if sig.get('name'):
                name_para = sig_cells[i].add_paragraph()
                name_run = name_para.add_run(sig['name'])
                name_run.bold = True

    def _remove_table_borders(self, table):
        """Remove borders from all cells in table"""
        from docx.oxml import parse_xml

        for row in table.rows:
            for cell in row.cells:
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))

    def _clear_cell_paragraphs(self, cell):
        """Clear all paragraphs in a cell"""
        for paragraph in cell.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)

    def _add_cell_top_padding(self, cell, padding='20'):
        """Add top padding to a cell"""
        from docx.oxml import parse_xml

        cell._tc.get_or_add_tcPr().append(parse_xml(
            f'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:top w:w="{padding}" w:type="dxa"/></w:tcMar>'))

    def _finalize_docx(self, doc, filename):
        """Save document và tạo attachment"""
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(doc_io.read()),
            'mimetype': 'application/vnd.openxmlformats-ocument.wordprocessingml.document'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }