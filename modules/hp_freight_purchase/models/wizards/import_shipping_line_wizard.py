from odoo import models, fields, _
from odoo.exceptions import UserError
import pandas as pd
import io
import base64
import re
import logging

_logger = logging.getLogger(__name__)

class ImportShippingLineWizard(models.TransientModel):
    _name = 'freight.purchase.import_shipping_line_wizard'
    _description = 'Import Shipping Line Wizard'

    file = fields.Binary(string='Upload File (Excel)', required=True)
    file_name = fields.Char(string='File Name')
    sheet_name = fields.Char(string='Sheet Name', help='Nhập tên sheet cần import (để trống sẽ lấy sheet đầu tiên)')

    def _validate_file(self, file_content):
        result = {
            'status': False,
            'message': '',
            'data': []
        }

        if not self.file_name.lower().endswith(('.xlsx', '.xls')):
            result['message'] = _("Chỉ chấp nhận file Excel (.xlsx, .xls).")
            return result

        engine = 'xlrd' if self.file_name.endswith('.xls') else 'openpyxl'
        convert_file_content = io.BytesIO(file_content)
        xl = pd.ExcelFile(convert_file_content, engine=engine)
        available_sheets = xl.sheet_names
        sheet_import = self.sheet_name or available_sheets[0]
        if sheet_import not in available_sheets:
            result['message'] = _('Không tìm thấy sheet "%s" trong file.') % self.sheet_name
            return result

        df = pd.read_excel(
            io.BytesIO(file_content),
            engine=engine,
            sheet_name=sheet_import,
            header=0
        )

        required_columns = ['STT', 'Tên hãng tàu', 'Email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            result['message'] = _('Thiếu các cột bắt buộc: %s') % ", ".join(missing_columns)
            return result

        partner_main_type = self.env.ref('hp_freight_purchase.partner_main_type_shipping_line',
                                         raise_if_not_found=False)
        if not partner_main_type:
            result['message'] = _('Không tìm thấy partner main type "shipping_line".')
            return result

        data = []
        for index, row in df.iterrows():
            name = row.get('Tên hãng tàu')
            email = row.get('Email')
            phone = row.get('Điện thoại')
            website = row.get('Website')
            address = row.get('Địa chỉ')
            notes = row.get('Ghi chú')

            if pd.isna(name) or not str(name).strip():
                continue

            name = re.sub(r'\s+', ' ', str(name).strip())

            if pd.isna(email) or not str(email).strip():
                email_slug = re.sub(r'[^\w\s-]', '', name)
                email_slug = re.sub(r'[-\s]+', '_', email_slug)
                email_slug = email_slug.strip().lower()
                email = f"{email_slug}@shipping-line.com"
            else:
                email = str(email).strip().lower()

            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                result['message'] = _('Email không hợp lệ tại dòng %s: %s') % (index + 2, email)
                return result

            phone = str(phone).strip() if pd.notna(phone) else ''
            website = str(website).strip() if pd.notna(website) else ''
            address = str(address).strip() if pd.notna(address) else ''
            notes = str(notes).strip() if pd.notna(notes) else ''

            data.append({
                'name': name,
                'email': email,
                'phone': phone,
                'website': website,
                'street': address,
                'comment': notes,
                'partner_main_type_id': partner_main_type.id,
                'is_company': True,
            })

        if not data:
            result['message'] = _('Không tìm thấy dữ liệu hợp lệ trong file.')
            return result

        return {
            'status': True,
            'message': '',
            'data': data
        }

    def _create_shipping_lines(self, data_array, batch_size=500):
        Partner = self.env['res.partner']
        domain = [('partner_main_type_id.code', '=', 'shipping_line')]

        # Lấy danh sách email + name để query theo batch
        emails = [d.get('email').lower() for d in data_array if d.get('email')]
        names = [d.get('name').lower() for d in data_array if d.get('name')]

        existing_by_email = {}
        existing_by_name = {}

        # Query theo batch email
        for i in range(0, len(emails), batch_size):
            batch_emails = emails[i:i + batch_size]
            partners = Partner.search(domain + [('email', 'in', batch_emails)])
            _logger.info("[IMPORT][Email Batch %s/%s] Found %s partners by email",
                         i // batch_size + 1, (len(emails) - 1) // batch_size + 1, len(partners))
            for p in partners:
                if p.email:
                    existing_by_email[p.email.lower()] = p

        # Query theo batch name
        for i in range(0, len(names), batch_size):
            batch_names = names[i:i + batch_size]
            partners = Partner.search(domain + [('name', 'in', batch_names)])
            _logger.info("[IMPORT][Name Batch %s/%s] Found %s partners by name",
                         i // batch_size + 1, (len(names) - 1) // batch_size + 1, len(partners))
            for p in partners:
                existing_by_name[p.name.lower()] = p

        to_create = []
        to_update = {}
        skipped = []

        for data in data_array:
            email_lower = data.get('email', '').lower()
            name_lower = data.get('name', '').lower()

            if email_lower in existing_by_email:
                partner = existing_by_email[email_lower]
                to_update[partner.id] = {
                    'name': data.get('name'),
                    'phone': data.get('phone'),
                    'website': data.get('website'),
                    'street': data.get('street'),
                    'comment': data.get('comment'),
                }
            else:
                if name_lower in existing_by_name:
                    skipped.append(data.get('name'))
                    continue
                to_create.append(data)

        created_count = 0
        updated_count = 0

        if to_create:
            created_partners = Partner.create(to_create)
            created_count = len(created_partners)
            _logger.info("[IMPORT] Created %s new partners in this batch.", created_count)

        if to_update:
            for partner_id, vals in to_update.items():
                Partner.browse(partner_id).write(vals)
            updated_count = len(to_update)
            _logger.info("[IMPORT] Updated %s existing partners in this batch.", updated_count)

        return {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped
        }

    def action_import(self):
        self.ensure_one()

        if not self.file:
            raise UserError(_('Vui lòng tải file lên.'))

        try:
            file_content = base64.b64decode(self.file)

            validate = self._validate_file(file_content)
            if not validate['status']:
                raise UserError(validate['message'])

            data = validate['data']
            batch_size = 1000

            total_created = 0
            total_updated = 0
            total_skipped = []

            _logger.info("[IMPORT] Start processing %s records (batch size: %s)", len(data), batch_size)

            for i in range(0, len(data), batch_size):
                batch_data = data[i:i + batch_size]
                _logger.info("[IMPORT] Processing batch %s/%s (%s records)",
                             i // batch_size + 1, (len(data) - 1) // batch_size + 1, len(batch_data))
                result = self._create_shipping_lines(batch_data)
                total_created += result['created']
                total_updated += result['updated']
                total_skipped.extend(result['skipped'])

            _logger.info("[IMPORT] Completed: created=%s, updated=%s, skipped=%s",
                         total_created, total_updated, len(total_skipped))

            message = _("Import thành công!\n"
                        "- Đã tạo mới: %s hãng tàu\n"
                        "- Đã cập nhật: %s hãng tàu") % (total_created, total_updated)

            if total_skipped:
                message += _("\n- Bỏ qua (trùng tên): %s") % ", ".join(set(total_skipped))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Thành Công'),
                    'message': message,
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            _logger.exception("[IMPORT] Error during import: %s", e)
            raise UserError(_('Lỗi: %s') % str(e))