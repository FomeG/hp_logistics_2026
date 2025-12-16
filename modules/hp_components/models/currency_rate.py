from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from reportlab.platypus.paraparser import sizeDelta

class CurrencyRate(models.Model):
    _name = 'currency.rate'
    _description = 'Currency Exchange Rate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, currency_id'

    currency_id = fields.Many2one(
        comodel_name='currency',
        string='Currency',
        required=True,
    )

    name = fields.Char(
        string='Display Name',
        compute='_compute_name',
        store=True
    )

    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
        index=True
    )

    rate = fields.Float(
        string='Exchange Rate',
        required=True,
        help='Exchange rate to base currency (1 base currency = X foreign currency)'
    )

    inverse_rate = fields.Float(
        string='Inverse Rate',
        compute='_compute_inverse_rate',
        store=True,
        help='Inverse exchange rate (1 foreign currency = X base currency)'
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    notes = fields.Text(
        string='Notes'
    )

    _sql_constraints = [
        ('unique_currency_date',
         'UNIQUE(currency_id, date, company_id)',
         'Only one rate per currency per date is allowed!'),
        ('rate_positive',
         'CHECK(rate > 0)',
         'Exchange rate must be positive!'),
    ]

    @api.depends('rate')
    def _compute_inverse_rate(self):
        """Tính tỷ giá nghịch đảo"""
        for record in self:
            if record.rate and record.rate != 0:
                record.inverse_rate = 1.0 / record.rate
            else:
                record.inverse_rate = 0.0

    @api.constrains('date', 'currency_id')
    def _check_future_date(self):
        """Cảnh báo nếu date trong tương lai"""
        for record in self:
            if record.date > fields.Date.today():
                raise ValidationError(_('Exchange rate date cannot be in the future!'))

    @api.depends('date', 'rate')
    def _compute_name(self):
        """Tính tên hiển thị"""
        for record in self:
            if record.date and record.rate:
                date_str = record.date.strftime('%d/%m/%Y')
                rate_str = f"{record.rate:,.2f}"
                record.name = f"{date_str} - {rate_str}"
            else:
                record.name = "New Rate"



