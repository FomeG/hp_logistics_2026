from odoo import models, fields, api
import logging
import json
import base64
import os
import uuid
from odoo.tools import config
_logger = logging.getLogger(__name__)


class MS365EmailStaging(models.Model):
    _name = 'ms365.email.staging'
    _description = 'MS365 Email Staging - Store emails for the day'
    _order = 'received_date desc'

    name = fields.Char(string='Subject', required=True)
    msg_id = fields.Char(string='MS365 Message ID', required=True, index=True)
    user_email = fields.Char(string='User Email', required=True, index=True)
    sender = fields.Char(string='From')
    body = fields.Html(string='Body')
    content_type = fields.Char(string='Content Type')
    received_date = fields.Datetime(string='Received Date', index=True)
    processed = fields.Boolean(string='Processed', default=False, index=True)
    partner_id = fields.Many2one('res.partner', string='Partner', index=True)

    # Dữ liệu cho attachments
    attachments_data = fields.Text(string='Attachments JSON')

    _sql_constraints = [
        ('unique_msg_id', 'unique(msg_id)', 'Message ID must be unique!')
    ]

    @api.model
    def clean_old_records(self):
        """Xóa các bản ghi cũ trước khi fetch mới"""
        # Xóa tất cả record cũ
        old_records = self.search([])
        old_records.unlink()
        _logger.info(f"Cleaned {len(old_records)} old staging records")
        return True

    @api.model
    def clone_to_mail_mail(self):
        """Clone dữ liệu từ staging sang mail.mail"""
        staging_records = self.search([('processed', '=', False)])

        mail_mail_obj = self.env['mail.mail'].sudo()
        created_count = 0

        for record in staging_records:
            try:
                # Kiểm tra xem đã tồn tại chưa
                existing = mail_mail_obj.search([
                    ('x_ms365_msg_id', '=', record.msg_id)
                ], limit=1)

                if existing:
                    record.processed = True
                    continue

                # Tạo mail.mail
                mail_mail = mail_mail_obj.create({
                    'subject': record.name,
                    'email_from': record.sender,
                    'email_to': record.user_email,
                    'state': 'sent',
                    'x_ms365_fetch': True,
                    'x_ms365_account': record.user_email,
                    'x_ms365_msg_id': record.msg_id,
                    'body_content': record.body,
                    'body_html': record.body,
                })

                # Xử lý attachments nếu có
                if record.attachments_data:
                    self._process_attachments(record, mail_mail)

                record.processed = True
                created_count += 1

            except Exception as e:
                _logger.warning(f"Error cloning record {record.id}: {e}")
                continue

        _logger.info(f"Cloned {created_count} emails to mail.mail")
        return True

    def _process_attachments(self, staging_record, mail_mail):
        """Xử lý attachments từ staging sang mail.mail"""
        module_path = os.path.dirname(os.path.abspath(__file__))
        parent_path = os.path.dirname(module_path)
        save_dir = os.path.join(parent_path, "ms365_files")

        try:
            attachments_list = json.loads(staging_record.attachments_data)
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', mail_mail.create_uid.id)
            ], limit=1)

            for att_data in attachments_list:
                file_name = att_data.get('name')
                file_content = att_data.get('content')
                mimetype = att_data.get('mimetype', 'application/octet-stream')

                if not file_content:
                    continue

                # Tạo file path
                file_name_safe = self._sanitize_filename(file_name)
                unique_name = f"{uuid.uuid4()}_{file_name_safe}"
                file_path = os.path.join(save_dir, unique_name)

                # Ghi file
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(file_content))

                # Đọc lại để encode
                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                # Tạo attachment
                attachment = self.env['ir.attachment'].sudo().create({
                    'name': file_name_safe,
                    'res_model': 'mail.mail',
                    'res_id': mail_mail.id,
                    'mimetype': mimetype,
                    'store_fname': file_path,
                    'file_size': os.path.getsize(file_path),
                    'datas': base64.b64encode(file_bytes).decode('utf-8'),
                })

                attachment.sudo().write({
                    'department': employee.department_id.name if employee and employee.department_id else '',
                })

                mail_mail.write({'unrestricted_attachment_ids': [(4, attachment.id)]})

        except Exception as e:
            _logger.warning(f"Error processing attachments: {e}")

    def _sanitize_filename(self, name):
        """Làm sạch tên file"""
        import re
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.replace('\n', '').replace('\r', '').strip()
        return name