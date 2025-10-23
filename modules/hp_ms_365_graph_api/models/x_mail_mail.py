from odoo import models,api,fields
class x_mail_mail(models.Model):
    _inherit = 'mail.mail'

    x_ms365_fetch = fields.Boolean(string='Fetch MS 365 data')
    x_ms365_account = fields.Char(string='MS 365 account')