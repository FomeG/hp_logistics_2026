from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import pandas as pd
import io
import re
import base64
from datetime import datetime

class ImportEmployeetWizard(models.TransientModel):
    _name = 'hp.import_employee_wizard'
    _description = 'Import employee Wizard'

    file = fields.Binary(string='Upload File (Excel)', required=True)
    file_name = fields.Char(string='File Name')
    sheet_name = fields.Char(string='Sheet Name',help='Select the Excel sheet to import')
    available_sheets = fields.Text(string='Available Sheets', readonly=True)

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

    def _validate_file(self, file_content):
        result = {
            'status': False,
            'message': '',
            'data': []
        }

        if not self.file_name.lower().endswith(('.xlsx', '.xls')):
            result['message'] = _("Only Excel files (.xlsx, .xls) are allowed.")
            return result

        engine = 'xlrd' if self.file_name.endswith('.xls') else 'openpyxl'
        convert_file_content = io.BytesIO(file_content)

        try:
            xl = pd.ExcelFile(convert_file_content, engine=engine)
            available_sheets = xl.sheet_names

            sheet_import = self.sheet_name or available_sheets[0]
            if sheet_import not in available_sheets:
                result['message'] = _('Sheet "%s" not found in file.\nAvailable sheets: %s') % (
                    sheet_import, ', '.join(available_sheets))
                return result

            df = pd.read_excel(
                io.BytesIO(file_content),
                engine=engine,
                sheet_name=sheet_import,
                header=1,
                dtype={'Phone': str}
            )

            required_columns = ['STT', 'Fullname', 'Email', 'Phone', 'Department Type', 'Branch']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                available_cols = [str(col) for col in df.columns]
                result['message'] = _('Missing required columns: %s\n\nAvailable columns in sheet "%s":\n%s') % (
                    ', '.join(missing_columns), sheet_import, '\n- '.join(available_cols))
                return result
            
            # Regex check
            email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            phone_regex = r'^\+?\d{9,15}$'

            # Query email employee, user
            existing_employee_emails = set(self.env['hr.employee'].search([]).mapped('work_email'))
            existing_user_emails = set(self.env['res.users'].search([]).mapped('login'))

            # Query department
            department_map = {}
            for d in self.env['hr.department'].search([]):
                key = (d.department_type_id.code, d.branch_id.code)
                department_map[key] = d.id

            errors = []
            processed_data = []
            for index, row in df.iterrows():
                line_no = index + 2
                row_errors = []

                name = str(row['Fullname']).strip() if pd.notna(row['Fullname']) else False
                email = str(row['Email']).strip() if pd.notna(row['Email']) else False
                phone = str(row['Phone']).strip() if pd.notna(row['Phone']) else False
                department_type = str(row['Department Type']).strip().lower() if pd.notna(row['Department Type']) else False
                branch = str(row['Branch']).strip().upper() if pd.notna(row['Branch']) else False

                # Validate data
                if not name:
                    row_errors.append(f"Name is not empty in line {line_no}")

                if not email:
                    row_errors.append(f"Email is not empty in line {line_no}")
                elif not re.match(email_regex, email):
                    row_errors.append(f"Email is incorrectly formatted in line {line_no}")
                elif email in existing_employee_emails or email in existing_user_emails:
                    row_errors.append(f"Email already exists in line {line_no}")

                if not phone:
                    row_errors.append(f"Phone is not empty in line {line_no}")
                elif not re.match(phone_regex, phone):
                    row_errors.append(f"Phone is incorrectly formatted in line {line_no}")

                if not department_type:
                    row_errors.append(f"Department is not empty in line {line_no}")
                if not branch:
                    row_errors.append(f"Branch is not empty in line {line_no}")

                # Valide date department exist
                dept_id = department_map.get((department_type, branch))
                if not dept_id:
                    row_errors.append(f"Department is not exist in line {line_no}")

                if row_errors:
                    errors.extend(row_errors)
                else:
                    processed_data.append({
                        'name': name,
                        'work_email': email,
                        'work_phone': phone,
                        'department_id': dept_id,
                    })

            if errors:
                result['message'] = "\n".join(errors)
                result['status'] = False
            else:
                result.update({
                    'status': True,
                    'data': processed_data,
                })

        except Exception as e:
            result['message'] = _('Error reading file: %s') % str(e)

        return result
        

    def action_import(self):
        self.ensure_one()
        try:
            if not self.file:
                raise UserError(_('Please upload a file.'))
        
            file_content = base64.b64decode(self.file)
            validate = self._validate_file(file_content)
            if not validate['status']:
                raise UserError(validate['message'])
            
            data = validate['data']
            self.env['hr.employee'].create(data)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Success'),
                    'message': _("Import success: %s employees") % len(data),
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(str(e))
