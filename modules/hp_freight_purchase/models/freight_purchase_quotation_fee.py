from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.quotation_fee_validator import QuotationFeeValidator


class FreightPurchaseQuotationFee(models.Model):
    _name = "freight.purchase.quotation.fee"
    _description = "Quotation Fee"

    quotation_id = fields.Many2one(
        comodel_name="freight.purchase.quotation",
        required=True,
        ondelete = "cascade"
    )
    fee_id = fields.Many2one(
        comodel_name="freight.purchase.fee",
        string="Fee",
        required=True,
        ondelete="cascade"

    )
    amount = fields.Float()
    note = fields.Char()


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = QuotationFeeValidator.validate(vals, self.env, mode='create')
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            validated, errors = QuotationFeeValidator.validate(vals, self.env, mode='write', record=record)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)
