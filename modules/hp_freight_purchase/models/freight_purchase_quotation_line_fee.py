from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.quotation_fee_validator import QuotationLineFeeValidator


class FreightPurchaseQuotationLineFee(models.Model):
    _name = "freight.purchase.quotation.line.fee"
    _description = "Quotation Line Fee"

    name = fields.Char(
        compute='_compute_name',
        store=False
    )

    quotation_line_id = fields.Many2one(
        comodel_name="freight.purchase.quotation.line",
        required=True
    )
    amount = fields.Float()

    shipping_line_id = fields.Many2one(
        related="quotation_line_id.quotation_id.shipping_line_id",
        store=True,
        readonly=True
    )
    direction = fields.Selection(
        related="quotation_line_id.quotation_id.direction",
        store=True,
        readonly=True
    )
    container_type_id = fields.Many2one(
        related="quotation_line_id.container_type_id",
        store=True,
        readonly=True
    )
    fee_line_id = fields.Many2one(
        comodel_name="freight.purchase.fee.line",
        required=True,
        domain="["
               "('shipping_line_id', '=', shipping_line_id),"
               "('container_type_id', '=', container_type_id),"
               "('fee_type_id.direction', '=', direction)"
               "]"
    )
    _sql_constraints = [
        ('unique_quotation_line_fee', 'unique(quotation_line_id, fee_line_id)', 'Fee already exists for this container.')
    ]

    @api.onchange('fee_line_id')
    def _onchange_fee_line_id(self):
        self.amount = self.fee_line_id.amount

    @api.depends('fee_line_id')
    def _compute_name(self):
        for record in self:
            if record.fee_line_id:
                record.name = f"{record.fee_line_id.fee_type_id.name or 'Fee'}: {record.amount}"
            else:
                record.name = "Fee"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = QuotationLineFeeValidator.validate(vals, self.env, mode='create')
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            validated, errors = QuotationLineFeeValidator.validate(vals, self.env, mode='write', current_id=record.id)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)
