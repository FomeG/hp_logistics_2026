from odoo import models, fields, api
from odoo.exceptions import UserError
from msal import ConfidentialClientApplication
import requests
import logging
import base64
from datetime import datetime, timedelta
from odoo import _
import os
import os, base64, uuid
import re
from odoo.tools import config
module_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(module_path)
save_dir = os.path.join(parent_path, "ms365_files")
os.makedirs(save_dir, exist_ok=True)

_logger = logging.getLogger(__name__)
class MsGraphMail(models.Model):
    _name = 'ms.graph.user'
    _description = 'Microsoft Graph Mail'

    subject = fields.Char("Subject")
    sender = fields.Char("From")
    body = fields.Text("Body")
    raw_data = fields.Text("Raw JSON")

    @api.model
    def _get_access_token(self):
        IrConfig = self.env['ir.config_parameter'].sudo()
        tenant_id = config.get('ms365_tenant_id') or IrConfig.get_param('ms365.tenant_id')
        client_id = config.get('ms365_client_id') or IrConfig.get_param('ms365.client_id')
        client_secret = config.get('ms365_client_secret') or IrConfig.get_param('ms365.client_secret')
        # tenant_id = "9e418708-ee71-4848-9d6d-f277ba7e59ea"
        # client_id = "bfa73233-816a-42bd-973f-fc7ae180ab95"
        # client_secret = "Z_R8Q~SMqgzZMX639zqJK0VttJZcLJS3BYHnLcRv"
        authority = f"https://login.microsoftonline.com/{tenant_id}"

        app = ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret
        )

        scope = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            raise UserError(f"Lấy token thất bại: {result}")
        return result["access_token"]

    def action_fetch_mail(self):

        """Button click gọi method này"""
        self.fetch_and_forward_mail()

    @api.model
    def fetch_and_forward_mail(self, forward_to="hn2722003@gmail.com"):
        """Lấy inbox của toàn bộ partner có email hợp lệ và forward sang Gmail"""
        partners = self.env['res.partner'].search([
            ('email', '!=', False)
        ])

        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        allowed_domain = "@hplogistics.com.vn"

        for partner in partners:
            email = (partner.email or "").strip().lower()

            # Chỉ nhận email đúng định dạng và đúng domain
            if not email or not email.endswith(allowed_domain):
                continue

            try:
                url = f"https://graph.microsoft.com/v1.0/users/{email}/mailFolders/Inbox/messages"
                r = requests.get(url, headers=headers)

                if r.status_code != 200:
                    # _logger.info(f"Bỏ qua {email}, không truy cập được inbox")
                    continue

                for e in r.json().get('value', []):
                    msg_id = e['id']
                    detail = requests.get(f"https://graph.microsoft.com/v1.0/users/{email}/messages/{msg_id}",
                                          headers=headers)

                    if detail.status_code != 200:
                        continue

                    msg = detail.json()
                    subject = msg.get('subject', '')
                    body = msg.get('body', {}).get('content', '')
                    content_type = msg.get('body', {}).get('contentType', 'Text')
                    sender = msg.get('from', {}).get('emailAddress', {}).get('address', '')

                    # Forward mail sang Gmail
                    send_url = f"https://graph.microsoft.com/v1.0/users/{email}/sendMail"
                    new_email = {
                        "message": {
                            "subject": f"FWD: {subject}",
                            "body": {"contentType": content_type, "content": body},
                            "toRecipients": [{"emailAddress": {"address": forward_to}}]
                        }
                    }
                    requests.post(send_url, headers=headers, json=new_email)

                    # self.env['mail.log'].create({
                    #     'partner_id': partner.id,
                    #     'subject': subject,
                    #     'sender': sender,
                    #     'body': body,
                    #     'raw_data': str(msg)
                    # })
            except Exception as e:
                # Không để cron fail, chỉ ghi log nhẹ nếu muốn
                # _logger.info(f"Lỗi xử lý email {email}: {e}")
                continue

        return True

    def fetch_and_forward_mail_single(self, forward_to="hn2722003@gmail.com"):
        partner = self.env.user.partner_id

        if not partner or not partner.email:
            raise UserError('Current User has no email in Partner record')

        user_email = partner.email.strip().lower()
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        return self._process_user_email(user_email, forward_to, headers)

    def sanitize_filename(self, name):
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.replace('\n', '').replace('\r', '').strip()
        return name

    def _process_user_email(self, user_email, forward_to, headers):
        # Tìm partner tương ứng với user_email để gắn vào chatter
        # Tạo thời gian từ đầu ngày đến cuối ngày (UTC)
        now_local = datetime.now()
        start_of_day_local = datetime(now_local.year, now_local.month, now_local.day, 0, 0, 0)
        end_of_day_local = datetime(now_local.year, now_local.month, now_local.day, 23, 59, 59)

        # Chuyển sang UTC (trừ 7 tiếng)
        start_utc = start_of_day_local - timedelta(hours=7)
        end_utc = end_of_day_local - timedelta(hours=7)

        start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        partner = self.env['res.partner'].search([('email', '=', user_email)], limit=1)
        url = (
            f"https://graph.microsoft.com/v1.0/users/{user_email}/mailFolders/Inbox/messages"
            f"?$filter=receivedDateTime ge {start_str} and receivedDateTime le {end_str}"
            f"&$orderby=receivedDateTime desc"
            f"&$top=50"
        )
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return False

        for e in r.json().get('value', []):
            msg_id = e['id']
            # raise UserError("id not available")
            detail = requests.get(
                f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{msg_id}",
                headers=headers
            )
            if detail.status_code != 200:
                continue

            msg = detail.json()
            subject = msg.get('subject', '')
            body = msg.get('body', {}).get('content', '')
            content_type = msg.get('body', {}).get('contentType', 'Text')
            sender = msg.get('from', {}).get('emailAddress', {}).get('address', '')
            #  Lưu vào mail.message thay vì forward

            # 1 Tạo mail.mail (cha) nếu muốn hiển thị trên list view mail.mail
            mail_mail = self.env['mail.mail'].create({
                'subject': subject,
                'email_from': sender,
                'email_to': forward_to,
                'state': 'sent',  # chỉ để hiển thị, không cần gửi
                'x_ms365_fetch': True,
                'body_content': body,
                'body_html': body,

                # 'create_uid' : user.id,
            })

            employee = self.env['hr.employee'].sudo().search([('user_id', '=', mail_mail.create_uid.id)], limit=1)

            # 2 Tạo mail.message (con) và liên kết với mail.mail
            message = self.env['mail.message'].create({
                'message_type': 'email',
                'subject': subject,
                'body': body,
                'model': 'res.partner' if partner else False,
                'res_id': partner.id if partner else False,
                # 'mail_message_id': mail_mail.id,
            })

            # Forward
            # send_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/sendMail"
            # new_email = {
            #     "message": {
            #         "subject": f"FWD: {subject}",
            #         "body": {"contentType": content_type, "content": body},
            #         "toRecipients": [{"emailAddress": {"address": forward_to}}]
            #     }
            # }
            # requests.post(send_url, headers=headers, json=new_email)
            #  Lấy danh sách file đính kèm
            attach_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{msg_id}/attachments"
            attach_res = requests.get(attach_url, headers=headers)
            if attach_res.status_code == 200:

                attachments = attach_res.json().get('value', [])
                for att in attachments:
                    if att.get('@odata.type') == '#microsoft.graph.fileAttachment':
                        file_name = att.get('name')
                        file_content = att.get('contentBytes')
                        mimetype = att.get('contentType', 'application/octet-stream')

                        if file_content:
                            try:
                                file_name_safe = self.sanitize_filename(file_name)
                                unique_name = f"{uuid.uuid4()}_{file_name_safe}"
                                file_path = os.path.join(save_dir, unique_name)

                                # Tạo folder nếu chưa có
                                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                                # Ghi file ra disk
                                with open(file_path, "wb") as f:
                                    f.write(base64.b64decode(file_content))

                                # Đọc lại file để encode vào datas
                                with open(file_path, "rb") as f:
                                    file_bytes = f.read()


                                attachment  = self.env['ir.attachment'].sudo().create({
                                    'name': file_name_safe,
                                    'res_model': 'mail.mail',
                                    'res_id': mail_mail.id,
                                    'mimetype': mimetype,
                                    'store_fname': file_path,
                                    'file_size': os.path.getsize(file_path),
                                    'datas': base64.b64encode(file_bytes).decode('utf-8'),
                                    # 'department': employee.department_id.name if employee.department_id else '',
                                })
                                attachment.sudo().write({
                                    'department': employee.department_id.name if employee.department_id else '',
                                })
                                # mail_mail.invalidate_recordset()
                                mail_mail.write({'unrestricted_attachment_ids': [(4, attachment.id)]})

                            except Exception as e:
                                _logger.warning(" Lỗi khi lưu attachment %s: %s", file_name, e)
        return True