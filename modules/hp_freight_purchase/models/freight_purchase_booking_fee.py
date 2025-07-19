from odoo import models, fields, api


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