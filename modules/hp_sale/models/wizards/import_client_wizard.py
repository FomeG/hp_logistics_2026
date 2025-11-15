from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import io
import base64
from datetime import datetime
from odoo.addons.hp_components.services.department_service import DepartmentService
from odoo.addons.hp_components.services.partner_service import PartnerService

class ImportClientWizard(models.TransientModel):
    _name = 'sale.import_client_wizard'
    _description = 'Import Client Wizard'

    branch_id = fields.Many2one('hr.branch', string='Branch', required=True)
    assign_user_id = fields.Many2one(
        'res.users',
        string='Assign User',
        required=True,
        domain="[('id', 'in', allowed_user_ids)]"
    )
    allowed_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_allowed_user_ids',
        store=False
    )
    file = fields.Binary(string='Upload File (Excel)', required=True)
    file_name = fields.Char(string='File Name')
    sheet_name = fields.Char(string='Sheet Name',help='Select the Excel sheet to import')
    available_sheets = fields.Text(string='Available Sheets', readonly=True)
    action_type = fields.Selection([
        (DepartmentService.DEPARTMENT_TYPE_SALE, 'Sale'),
        (DepartmentService.DEPARTMENT_TYPE_TRUCKING, 'Trucking')
    ], string='Action Type')

    @api.depends('branch_id', 'action_type')
    def _compute_allowed_user_ids(self):
        for wizard in self:
            wizard.allowed_user_ids = DepartmentService(self.env).get_user_by_department_type(self.action_type, self.branch_id.id)

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.assign_user_id = False

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
                header=3
            )

            required_columns = ['Mã đối tượng', 'MST', 'Tên đối tượng', 'ĐỊA CHỈ']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                available_cols = [str(col) for col in df.columns]
                result['message'] = _('Missing required columns: %s\n\nAvailable columns in sheet "%s":\n%s') % (
                    ', '.join(missing_columns), sheet_import, '\n- '.join(available_cols))
                return result

            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            processed_data = []
            fake_data_count = 0

            for index, row in df.iterrows():
                tax_number = str(row['MST']).strip() if pd.notna(row['MST']) else f'FAKE_{current_time}_{index}'
                ref = str(row['Mã đối tượng']).strip() if pd.notna(
                    row['Mã đối tượng']) else f'FAKE_{current_time}_{index}'
                name = str(row['Tên đối tượng']).strip() if pd.notna(
                    row['Tên đối tượng']) else f'FAKE_{current_time}_{index}'
                address = str(row['ĐỊA CHỈ']).strip() if pd.notna(row['ĐỊA CHỈ']) else False
                phone = str(row.get('Số điện thoại', '')).strip() if pd.notna(row.get('Số điện thoại')) else False

                if tax_number.startswith('FAKE_') or ref.startswith('FAKE_') or name.startswith('FAKE_'):
                    fake_data_count += 1

                processed_data.append({
                    'ref': ref,
                    'name': name,
                    'street': address,
                    'vat': tax_number,
                    'phone': phone,
                })

            result.update({
                'status': True,
                'data': processed_data,
                'sheet_name': sheet_import,
                'fake_data_count': fake_data_count,
                'current_time': current_time
            })

        except Exception as e:
            result['message'] = _('Error reading file: %s') % str(e)

        return result

    def _create_clients(self, data_array):
        branch = self.env['hr.branch'].search([('code', '=', self.branch_id.code)], limit=1)
        if not branch:
            raise UserError("Branch not found")
        Client = self.env['res.partner.client']
        tax_numbers = [data['vat'] for data in data_array]
        refs = [data['ref'] for data in data_array]
        existing_partners = self.env['res.partner'].search([('vat', 'in', tax_numbers)])
        existing_vats = {partner.vat for partner in existing_partners}
        existing_clients = Client.search([
            '|', ('vat', 'in', tax_numbers), ('ref', 'in', refs)
        ])
        existing_clients_map = {client.vat: client for client in existing_clients}

        clients_to_create = []
        clients_to_update = []
        skipped_vats = []

        for data in data_array:
            vals = data.copy()
            vat = data['vat']
            ref = data['ref']

            if vat in existing_vats and vat not in existing_clients_map:
                skipped_vats.append(vat)
                continue

            partner_service = PartnerService(self.env)
            partner_main_type = partner_service.get_partner_main_type_client()
            vals.update({
                'partner_main_type_id': partner_main_type.id,
                'branch_id': self.branch_id.id,
                'user_id':  self.assign_user_id.id if self.action_type == DepartmentService.DEPARTMENT_TYPE_SALE else False,
            })
            existing_client = existing_clients_map.get(vat) or Client.search([('ref', '=', ref)], limit=1)
            if existing_client:
                clients_to_update.append((existing_client, vals))
            else:
                clients_to_create.append(vals)
                   

        imported_count = 0
        updated_count = 0
        skipped_count = len(skipped_vats)

        if clients_to_create:
            Client.create(clients_to_create)
            imported_count = len(clients_to_create)

        if clients_to_update:
            for existing_client, vals in clients_to_update:
                if self.action_type == DepartmentService.DEPARTMENT_TYPE_TRUCKING:
                    vals.pop('user_id')
                
                if self.action_type == DepartmentService.DEPARTMENT_TYPE_SALE:
                    vals.pop('assign_trucking_manager_id')
                    if existing_client.user_id:
                        vals.pop('user_id')

                existing_client.write(vals)
            updated_count = len(clients_to_update)

        return imported_count, updated_count, skipped_count, skipped_vats

    def action_import(self):
        self.ensure_one()
        try:
            if not self.file:
                raise UserError(_('Please upload a file.'))
            file_content = base64.b64decode(self.file)
            validate_result = self._validate_file(file_content)
            if not validate_result['status']:
                raise UserError(validate_result['message'])

            data = validate_result['data']
            if not data:
                raise UserError(_('No valid data found to import.'))

            imported_count, updated_count, skipped_count, skipped_vats = self._create_clients(data)

            message_parts = [
                _('Import completed from sheet "%s"') % validate_result['sheet_name'],
                _('- New clients: %s') % imported_count,
                _('- Updated clients: %s') % updated_count,
            ]

            fake_data_count = validate_result.get('fake_data_count', 0)
            if fake_data_count > 0:
                current_time = validate_result.get('current_time', '')
                message_parts.append(_('- Records with fake data (FAKE_%s_*): %s') % (current_time, fake_data_count))

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

        except Exception as e:
            raise UserError(str(e))