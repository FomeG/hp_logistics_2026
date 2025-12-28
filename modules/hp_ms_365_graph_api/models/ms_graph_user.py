from odoo import models, fields, api
from odoo.exceptions import UserError
from msal import ConfidentialClientApplication
import requests
import logging
import base64
from datetime import datetime, timedelta, timezone
from odoo import _
import os
import os, base64, uuid
import re
import json
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
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True,
        index=True
    )
    x_has_fetched_all = fields.Boolean(
        string='Has Fetched All Emails',
        default=False,
        help='If True, only fetch today emails. If False, fetch last 90 days.'
    )
    _sql_constraints = [
        ('unique_user_id', 'unique(user_id)', 'Each user can only have one MS Graph record!')
    ]

    @api.model
    def action_open_my_profile(self):
        current_user = self.env.user

        # Tìm record của user này
        ms_user = self.search([('user_id', '=', current_user.id)], limit=1)

        if not ms_user:
            ms_user = self.create({
                'user_id': current_user.id,
                'x_has_fetched_all': False
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ms.graph.user',
            'res_id': ms_user.id,
            'view_mode': 'form',
            'target': 'current',
            'name': 'My MS365 Profile',
        }

    @api.model
    def _get_access_token(self):
        IrConfig = self.env['ir.config_parameter'].sudo()
        tenant_id = config.get('ms365_tenant_id') or IrConfig.get_param('ms365.tenant_id')
        client_id = config.get('ms365_client_id') or IrConfig.get_param('ms365.client_id')
        client_secret = config.get('ms365_client_secret') or IrConfig.get_param('ms365.client_secret')

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
    def fetch_and_forward_mail(self):
        """
        CẬP NHẬT: Fetch email và lưu vào staging table
        - Clean staging table trước
        - Fetch email từ MS365
        - Lưu vào staging table
        - Clone từ staging sang mail.mail
        """
        IrConfig = self.env['ir.config_parameter'].sudo()
        forward_to = config.get('ms365.forward_to') or IrConfig.get_param('ms365.forward_to')

        users = self.env['res.users'].search([
            ('login', '!=', False),
            ('active', '=', True)
        ])
        # partners = self.env['res.partner'].search([
        #     ('email', '!=', False)
        # ])
        # _logger.info(f"🔎 Forward email to: {forward_to}")

        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        # Lọc email trong 2 ngày gần nhất
        now_utc = datetime.now(timezone.utc)
        since_time = (now_utc - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        allowed_domain = "@hplogistics.com.vn"

        # 1. Clean staging table
        self.env['ms365.email.staging'].clean_old_records()

        staging_obj = self.env['ms365.email.staging'].sudo()

        for user in users:
            email = (user.login or "").strip().lower()

            # Chỉ nhận email đúng định dạng và đúng domain
            if not email or not email.endswith(allowed_domain):
                continue

            try:
                url = (
                    f"https://graph.microsoft.com/v1.0/users/{email}/mailFolders/Inbox/messages"
                    f"?$filter=receivedDateTime ge {since_time}"
                    f"&$orderby=receivedDateTime desc&$top=50"
                )
                r = requests.get(url, headers=headers)

                if r.status_code != 200:
                    continue

                for e in r.json().get('value', []):
                    msg_id = e['id']
                    if not msg_id:
                        continue
                    # Check trong staging
                    existing_staging = staging_obj.search([('msg_id', '=', msg_id)], limit=1)
                    if existing_staging:
                        continue  # Đã có trong staging

                    # Check mail.mail
                    existing_mail = self.env['mail.mail'].sudo().search([
                        ('x_ms365_msg_id', '=', msg_id)
                    ], limit=1)
                    if existing_mail:
                        continue  # Đã fetch rồi

                    # Lấy chi tiết email
                    detail = requests.get(
                        f"https://graph.microsoft.com/v1.0/users/{email}/messages/{msg_id}",
                        headers=headers
                    )

                    if detail.status_code != 200:
                        continue

                    msg = detail.json()
                    subject = msg.get('subject', '')
                    body = msg.get('body', {}).get('content', '')
                    content_type = msg.get('body', {}).get('contentType', 'Text')
                    sender = msg.get('from', {}).get('emailAddress', {}).get('address', '')
                    received_date_str = msg.get('receivedDateTime', '')
                    received_date = datetime.fromisoformat(
                        received_date_str.replace('Z', '+00:00')) if received_date_str else False

                    # Lấy attachments
                    attachments_data = self._fetch_attachments(email, msg_id, headers)

                    # Tìm partner từ user
                    partner = user.partner_id

                    # Lưu vào staging
                    staging_obj.create({
                        'name': subject,
                        'msg_id': msg_id,
                        'user_email': email,
                        'sender': sender,
                        'body': body,
                        'content_type': content_type,
                        'received_date': received_date,
                        'partner_id': partner.id if partner else False,
                        'attachments_data': json.dumps(attachments_data) if attachments_data else False,
                    })

            except Exception as e:
                _logger.warning(f"Lỗi xử lý email {email}: {e}")
                continue

        # 2. Clone từ staging sang mail.mail
        self.env['ms365.email.staging'].clone_to_mail_mail()

        return True

    def _fetch_attachments(self, user_email, msg_id, headers):
        """Lấy thông tin attachments và trả về dạng list of dict"""
        attachments_list = []

        try:
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
                            attachments_list.append({
                                'name': file_name,
                                'content': file_content,
                                'mimetype': mimetype
                            })
        except Exception as e:
            _logger.warning(f"Error fetching attachments for {msg_id}: {e}")

        return attachments_list

    def fetch_and_forward_mail_single(self):
        """
        CẬP NHẬT: Fetch email của user hiện tại với logic thông minh
        - Nếu x_has_fetched_all = False: fetch 90 ngày gần nhất và set flag = True
        - Nếu x_has_fetched_all = True: chỉ fetch email trong ngày
        """
        IrConfig = self.env['ir.config_parameter'].sudo()
        forward_to = config.get('ms365.forward_to') or IrConfig.get_param('ms365.forward_to')
        # partner = self.env.user.partner_id

        # if not partner or not partner.email:
        #     raise UserError('Current User has no email in Partner record')
        #
        # user_email = partner.email.strip().lower()
        # Dùng user.login thay vì partner.email
        user = self.env.user
        user_email = (user.login or "").strip().lower()

        if not user_email:
            raise UserError('User không có login email')
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Xác định số ngày cần fetch
        if not self.x_has_fetched_all:
            days_to_fetch = 90
            _logger.info(f"📧 First time fetch for {user_email} - fetching last 90 days")
        else:
            days_to_fetch = 1
            _logger.info(f"📧 Regular fetch for {user_email} - fetching today only")

        result = self._process_user_email(user_email, forward_to, headers, days_to_fetch)

        if result and not self.x_has_fetched_all:
            self.write({'x_has_fetched_all': True, 'user_id': self.env.user.id})
        return result

    def sanitize_filename(self, name):
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.replace('\n', '').replace('\r', '').strip()
        return name

    def _process_user_email(self, user_email, forward_to, headers, days_to_fetch=1):
        """
        CẬP NHẬT: Xử lý email với tham số days_to_fetch
        """
        # Tạo thời gian từ đầu ngày đến cuối ngày (UTC)
        now_local = datetime.now()
        start_of_day_local = datetime(now_local.year, now_local.month, now_local.day, 0, 0, 0)
        end_of_day_local = datetime(now_local.year, now_local.month, now_local.day, 23, 59, 59)

        # Chuyển sang UTC (trừ 7 tiếng)
        start_utc = start_of_day_local - timedelta(hours=7) - timedelta(days=days_to_fetch - 1)
        end_utc = end_of_day_local - timedelta(hours=7)

        start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Tìm user từ login
        user = self.env['res.users'].search([('login', '=', user_email)], limit=1)
        partner = user.partner_id if user else False
        # partner = self.env['res.partner'].search([('email', '=', user_email)], limit=1)
        url = (
            f"https://graph.microsoft.com/v1.0/users/{user_email}/mailFolders/Inbox/messages"
            f"?$filter=receivedDateTime ge {start_str} and receivedDateTime le {end_str}"
            f"&$orderby=receivedDateTime desc"
            f"&$top=50"
        )
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return False

        staging_obj = self.env['ms365.email.staging'].sudo()

        for e in r.json().get('value', []):
            msg_id = e['id']
            # Check trong staging
            existing_staging = staging_obj.search([('msg_id', '=', msg_id)], limit=1)
            if existing_staging:
                continue

            # Check mail.mail sau
            existing_mail = self.env['mail.mail'].sudo().search([
                ('x_ms365_msg_id', '=', msg_id)
            ], limit=1)
            if existing_mail:
                continue

            # Lấy chi tiết
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
            received_date_str = msg.get('receivedDateTime', '')
            received_date = datetime.fromisoformat(received_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            # Lấy attachments
            attachments_data = self._fetch_attachments(user_email, msg_id, headers)
            # Lưu vào staging
            staging_obj.create({
                'name': subject,
                'msg_id': msg_id,
                'user_email': user_email,
                'sender': sender,
                'body': body,
                'content_type': content_type,
                'received_date': received_date,
                'partner_id': partner.id if partner else False,
                'attachments_data': json.dumps(attachments_data) if attachments_data else False,
            })
        # Clone từ staging sang mail.mail
        self.env['ms365.email.staging'].clone_to_mail_mail()
        return True