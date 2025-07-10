from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import FeeValidator

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
        comodel_name='res.partner',
        domain="[('is_shipping_line', '=', True)]",
        required=True,
        index=True,
    )
    fee_type_id = fields.Many2one(
        comodel_name='freight.purchase.fee.type',
        domain="[('is_common', '=', False)]",
        required=True,
        index=True,
    )
    route_id = fields.Many2one(
        comodel_name="freight.purchase.route",
        required=False
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
        string='Container Fee'
    )

    total_container_fees = fields.Char(
        string="Total Container Fees",
        compute='_compute_total_container_fees',
        store=False
    )


    @api.depends('line_ids')
    def _compute_total_container_fees(self):
        for record in self:
            if record.line_ids:
                total = len(record.line_ids)
                record.total_container_fees = f"{total} Fee(s)"
            else:
                record.total_container_fees = "0 Fee"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = FeeValidator.validate_fee(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):

        current_record = self if isinstance(self, type(self)) else self[0]
        validated, errors = FeeValidator.validate_fee(vals,self.env,mode='write',record=current_record)
        if errors:
            raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)

    @api.depends('shipping_line_id', 'fee_type_id','date_from')
    def _compute_name(self):
        for record in self:
            date_str = record.date_from.strftime('%d-%m-%Y') if record.date_from else ''
            record.name = f"{record.shipping_line_id.name or ''} - {record.fee_type_id.name or ''} - {date_str}".strip(
                ' -')

    @api.constrains('fee_type_id', 'shipping_line_id', 'date_from')
    def _check_unique_fee_period(self):
        for record in self:
            domain = [
                ('fee_type_id', '=', record.fee_type_id.id),
                ('shipping_line_id', '=', record.shipping_line_id.id),
                ('id', '!=', record.id)
            ]

            if record.date_from:
                domain.append(('date_from', '=', record.date_from))
            else:
                domain.append(('date_from', '=', False))

            if self.search_count(domain) > 0:
                raise ValidationError(f"Fee already exists for this shipping line and period.")