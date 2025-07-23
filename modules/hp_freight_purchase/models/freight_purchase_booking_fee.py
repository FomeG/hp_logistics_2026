from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.booking_fee_validator import BookingFeeValidator


class FreightPurchaseBookingFee(models.Model):
    _name = "freight.purchase.booking.fee"
    _description = "Booking Fee"

    booking_id = fields.Many2one(
        comodel_name="freight.purchase.booking",
        required=True
    )
    fee_type_id = fields.Many2one(
        comodel_name="freight.purchase.fee.type",
        domain="[('is_common', '=', True)]",
        required=True
    )
    amount = fields.Float()
    note = fields.Char()

    @api.onchange('fee_type_id')
    def onchange_fee_type(self):
        self.amount = self.fee_type_id.amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = BookingFeeValidator.validate(vals, self.env, mode='create')
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            validated, errors = BookingFeeValidator.validate(vals, self.env, mode='write', current_id=record.id)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals) 