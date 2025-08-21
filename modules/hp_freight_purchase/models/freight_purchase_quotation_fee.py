from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.quotation_fee_validator import QuotationFeeValidator


class FreightPurchaseQuotationFee(models.Model):
    _name = "freight.purchase.quotation.fee"
    _description = "Quotation Fee"

    quotation_id = fields.Many2one(
        comodel_name="freight.purchase.quotation",
        required=True
    )
    fee_id = fields.Many2one(
        comodel_name="freight.purchase.fee",
        string="Fee",
        required=True,
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

    # @api.onchange('quotation_id')
    # def _onchange_quotation_id(self):
    #     if not self.quotation_id:
    #         return
    #
    #     quotation_route = self.quotation_id.route_id
    #     if not quotation_route:
    #         return
    #
    #     # Lọc fee theo shipping line và route trùng
    #     domain = [
    #         ('shipping_line_id', '=', self.quotation_id.shipping_line_id.id),
    #         ('route_id', '=', quotation_route.id),
    #     ]
    #     # direction OR N/A
    #     domain += ['|', ('direction', '=', quotation_route.direction), ('direction', '=', False)]
    #
    #     return {'domain': {'fee_id': domain}}
