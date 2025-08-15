from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import io
import base64
from odoo.addons.hp_components.services.department_service import DepartmentService

class ImportClientWizard(models.TransientModel):
    _name = 'trucking_planning.import_client_wizard'
    _description = 'Import Client Wizard'

    branch_id = fields.Many2one('trucking_planning.branch', string='Branch', required=True)
    assign_user_id = fields.Many2one(
        'res.users',
        string='Assign User',
        required=True,
        domain=lambda self: self._get_assign_user_domain()
    )
    file = fields.Binary(string='Upload File (Excel)', required=True)
    file_name = fields.Char(string='File Name')
    sheet_name = fields.Char(string='Sheet Name',help='Select the Excel sheet to import')
    available_sheets = fields.Text(string='Available Sheets', readonly=True)

    @api.model
    def _get_assign_user_domain(self):
        allow_assign_users = DepartmentService(self.env).get_user_by_department_type('trucking')
        return [('id', 'in', allow_assign_users.ids)]

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.assign_user_id = False
        allow_assign_users = DepartmentService(self.env).get_user_by_department_type('trucking')
        if self.branch_id:
            allowed_users = allow_assign_users.filtered(lambda u: u.id in self.branch_id.user_ids.ids)
        else:
            allowed_users = allow_assign_users
        return {
            'domain': {'assign_user_id': [('id', 'in', allowed_users.ids)]}
        }

    @api.onchange('file', 'file_name')
    def _onchange_file(self):
        if self.file and self.file_name:
            self.sheet_name = ''
            try:
                file_content = base64.b64decode(self.file)
                xl = pd.ExcelFile(io.BytesIO(file_content),
                                  engine='xlrd' if self.file_name.endswith('.xls') else 'openpyxl')
                self.available_sheets = ', '.join(xl.sheet_names)
                if len(xl.sheet_names) >= 1:
                    self.sheet_name = xl.sheet_names[0]
            except Exception:
                self.available_sheets = 'Cannot read Excel file'
        else:
            self.sheet_name = ''
            self.available_sheets = ''

    def get_available_sheets(self):
        if not self.file or not self.file_name:
            return []
        try:
            file_content = base64.b64decode(self.file)
            xl = pd.ExcelFile(io.BytesIO(file_content),
                              engine='xlrd' if self.file_name.endswith('.xls') else 'openpyxl')
            return xl.sheet_names
        except Exception:
            return []

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_('Please upload a file.'))
        try:
            file_content = base64.b64decode(self.file)
            xl = pd.ExcelFile(io.BytesIO(file_content),
                              engine='xlrd' if self.file_name.endswith('.xls') else 'openpyxl')
            sheet_names = xl.sheet_names
            sheet_to_import = None

            if self.sheet_name:
                if self.sheet_name in sheet_names:
                    sheet_to_import = self.sheet_name
                else:
                    raise UserError(_('Sheet "%s" not found in file.\nAvailable sheets: %s') % (
                    self.sheet_name, ', '.join(sheet_names)))
            else:
                if len(sheet_names) == 1:
                    sheet_to_import = sheet_names[0]
                else:
                    raise UserError(
                        _('Multiple sheets found. Please specify sheet name.\nAvailable sheets: %s') % ', '.join(
                            sheet_names))

            df = pd.read_excel(io.BytesIO(file_content),
                               engine='xlrd' if self.file_name.endswith('.xls') else 'openpyxl',
                               sheet_name=sheet_to_import,
                               header=3)

        except Exception as e:
            raise UserError(_('Error reading file: %s') % str(e))

        required_columns = ['Mã đối tượng', 'MST', 'Tên đối tượng', 'ĐỊA CHỈ']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            available_cols = [str(col) for col in df.columns]
            raise UserError(_('Missing required columns: %s\n\nAvailable columns in sheet "%s":\n%s') %
                            (', '.join(missing_columns), sheet_to_import, '\n- '.join(available_cols)))
        client_model = self.env['trucking_planning.client']
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            tax_number = str(row['MST']).strip() if pd.notna(row['MST']) else False
            if not tax_number:
                skipped_count += 1
                continue

            existing_client = client_model.search([('tax_number', '=', tax_number)], limit=1)
            vals = {
                'code': str(row['Mã đối tượng']).strip() if pd.notna(row['Mã đối tượng']) else False,
                'name': str(row['Tên đối tượng']).strip() if pd.notna(row['Tên đối tượng']) else False,
                'address': str(row['ĐỊA CHỈ']).strip() if pd.notna(row['ĐỊA CHỈ']) else False,
                'tax_number': tax_number,
                'branch_id': self.branch_id.id,
                'assign_user_id': self.assign_user_id.id,
                'phone': str(row.get('Số điện thoại', '')).strip() if pd.notna(row.get('Số điện thoại')) else False,
            }

            if existing_client:
                existing_client.write(vals)
                updated_count += 1
            else:
                client_model.create(vals)
                imported_count += 1

        message_parts = [
            _('Import completed from sheet "%s"') % sheet_to_import,
            _('- New clients: %s') % imported_count,
            _('- Updated clients: %s') % updated_count,
        ]

        if skipped_count > 0:
            message_parts.append(_('- Skipped rows (no tax number): %s') % skipped_count)

        message = '\n'.join(message_parts)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Success'),
                'message': message,
                'sticky': False,
            }
        }