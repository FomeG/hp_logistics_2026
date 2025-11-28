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

    def _add_docx_header(self, doc, header_data):
        """Thêm header vào document."""
        pass

    def _add_docx_body(self, doc, body_data):
        """Thêm body content vào document."""
        pass

    def _add_docx_footer(self, doc, footer_data):
        """Thêm footer/signature vào document."""
        pass

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