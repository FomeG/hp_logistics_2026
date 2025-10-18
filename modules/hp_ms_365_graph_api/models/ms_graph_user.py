from odoo import models, fields, api
from odoo.exceptions import UserError
from msal import ConfidentialClientApplication
import requests
import logging
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
        tenant_id = "9e418708-ee71-4848-9d6d-f277ba7e59ea"
        client_id = "bfa73233-816a-42bd-973f-fc7ae180ab95"
        client_secret = "Z_R8Q~SMqgzZMX639zqJK0VttJZcLJS3BYHnLcRv"
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

        # -------------------------------------------
        # 4. Hàm xử lý chung để tránh lặp code
        # -------------------------------------------

    def _process_user_email(self, user_email, forward_to, headers):
        url = f"https://graph.microsoft.com/v1.0/users/{user_email}/mailFolders/Inbox/messages"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return False

        for e in r.json().get('value', []):
            msg_id = e['id']
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

            # Forward
            send_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/sendMail"
            new_email = {
                "message": {
                    "subject": f"FWD: {subject}",
                    "body": {"contentType": content_type, "content": body},
                    "toRecipients": [{"emailAddress": {"address": forward_to}}]
                }
            }
            requests.post(send_url, headers=headers, json=new_email)

        return True