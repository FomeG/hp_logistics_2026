from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from reportlab.platypus.paraparser import sizeDelta


class Currency(models.Model):
    _name = 'currency'
    _description = 'Currency'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin']
    _order = 'sequence asc, name asc'

    name = fields.Char(
        string='Currency Name',
        required=True,
        help="The name of the currency. (e.g., US Dollar, Euro)",
    )

    code = fields.Char(
        string='Currency Code',
        required=True,
        size=3,
        help="The three-letter ISO code of the currency. (e.g., USD, EUR)"
    )

    symbol = fields.Char(
        string='Currency Symbol',
        required=True,
        size=10,
        help="The symbol used to represent the currency. (e.g., $, €)"
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )

    is_base_currency = fields.Boolean(
        string='Is Base Currency',
        default=False,
        help="Indicates if this currency is the base currency for the company.",
    )

    rate_ids = fields.One2many(
        comodel_name='currency.rate',
        inverse_name='currency_id',
        string='Exchange Rates',
    )

    current_rate = fields.Float(
        string='Current Exchange Rate',
        compute='_compute_current_rate',
        store=False,
        help="The most recent exchange rate for this currency.",
    )

    @api.depends('rate_ids.date')
    def _compute_current_rate(self):
        """Lấy tỷ giá hiện tại (mới nhất) của currency"""
        for currency in self:
            latest_rate = self.env['currency.rate'].search([
                ('currency_id', '=', currency.id),
                ('date', '<=', fields.Date.today())
            ], order='date desc', limit=1)
            currency.current_rate = latest_rate.rate if latest_rate else 1.0


    @api.constrains('is_base_currency')
    def _check_single_base_currency(self):
        """Đảm bảo chỉ có 1 base currency"""
        for record in self:
            if record.is_base_currency:
                other_base = self.search([
                    ('is_base_currency', '=', True),
                    ('id', '!=', record.id)
                ])
                if other_base:
                    raise ValidationError(_('Only one currency can be set as base currency!'))

    def get_rate(self, date=None):
        """Lấy tỷ giá tại một ngày cụ thể"""
        self.ensure_one()
        if not date:
            date = fields.Date.today()

        rate = self.env['currency.rate'].search([
            ('currency_id', '=', self.id),
            ('date', '<=', date)
        ], order='date desc', limit=1)

        return rate.rate if rate else 1.0

    def convert_to(self, amount, target_currency, date=None):
        """Chuyển đổi số tiền từ currency này sang currency khác"""
        self.ensure_one()
        if not date:
            date = fields.Date.today()

        # Nếu cùng currency thì không cần convert
        if self.id == target_currency.id:
            return amount

        # Lấy tỷ giá của cả 2 currency
        from_rate = self.get_rate(date)
        to_rate = target_currency.get_rate(date)

        # Convert: amount * (from_rate / to_rate)
        if to_rate == 0:
            raise ValidationError(_('Target currency rate cannot be zero!'))

        return amount * (from_rate / to_rate)

    @api.model
    def get_rate_for_currency(self, currency_id, date=None):
        """Helper method để lấy tỷ giá cho currency tại một ngày"""
        if not date:
            date = fields.Date.today()

        rate = self.search([
            ('currency_id', '=', currency_id),
            ('date', '<=', date)
        ], order='date desc', limit=1)

        return rate.rate if rate else 1.0