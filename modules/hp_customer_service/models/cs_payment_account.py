from odoo import models, fields

class CSPaymentAccount(models.Model):
    _name = "cs.payment.account"
    _description = "Thông tin tài khoản thanh toán"

    name = fields.Char(string="Tên tài khoản", required=True)
    account_number = fields.Char(string="Số tài khoản", required=True)
    bank_name = fields.Char(string="Tên ngân hàng", required=True)
    type = fields.Selection([
        ('company', 'Tài khoản công ty'),
        ('personal', 'Tài khoản cá nhân'),
    ], string="Loại tài khoản", default="company")
