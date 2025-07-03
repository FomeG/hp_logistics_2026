from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import  FeeValidator

class FreightPurchaseFee(models.Model):
    _name = 'freight.purchase.fee'
    _description = 'Additional Fee from Shipping Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    name = fields.Char(
        'Name',
        readonly=True,
        compute='_compute_name',
        store=True,
    )
    shipping_line_id = fields.Many2one(
        'res.partner',
        domain="[('is_shipping_line', '=', True)]",
        required=True
    )
    fee_type_id = fields.Many2one(
        'freight.purchase.fee.type',
        required=True,
    )
    date_from = fields.Date(
        required=False,
        tracking=True,
        index=True,
    )
    date_to = fields.Date(
        required=False,
        tracking=True,
        index=True
    )
    note = fields.Text()
    line_ids = fields.One2many(
        'freight.purchase.fee.line',
        'fee_id',
        string='Container Charges'
    )

    _sql_constraints = [
        ('unique_fee_period', 'unique(fee_type_id, shipping_line_id, date_from, date_to)', 'Fee already exists for this shipping line and period.')
    ]
    quotations = fields.Many2many('freight.purchase.quotation', string='Quotations')
    total_quotation = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)

    @api.depends('quotations')
    def _compute_total_quotation(self):
        for record in self:
            if record.quotations:
                total = len(record.quotations)
                record.total_quotation = f"{total} Quotation(s)"
            else:
                record.total_quotation = "0 Quotation(s)"


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = FeeValidator.validate_fee(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            validated, errors = FeeValidator.validate_fee(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)

    @api.depends('shipping_line_id', 'fee_type_id','date_from')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.shipping_line_id.name or ''} - {record.fee_type_id.name or ''} - {record.date_from.strftime('%d-%m-%Y') or ''}".strip(' -')