from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.booking_fee_validator import BookingLineFeeValidator


class FreightPurchaseBookingLineFee(models.Model):
    _name = "freight.purchase.booking.line.fee"
    _description = "Booking Line Fee"

    name = fields.Char(
        compute='_compute_name',
        store=False
    )

    booking_line_id = fields.Many2one(
        comodel_name="freight.purchase.booking.line",
        required=True,
        ondelete='cascade',
    )
    fee_line_id = fields.Many2one(
        comodel_name="freight.purchase.fee.line",
        string='Fee Line',
        required=True,
        domain="[('shipping_line_id', '=', shipping_line_id), '|', ('container_type_id', '=', container_type_id), ('container_type_id', '=', False)]"
    )
    amount = fields.Float(
        string='Amount',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='fee_line_id.currency_id',
        store=True,
        readonly=True,
    )

    # Related fields for domain filtering
    shipping_line_id = fields.Many2one(
        related="booking_line_id.booking_id.shipping_line_id",
        store=True,
        readonly=True,
    )
    container_type_id = fields.Many2one(
        related="booking_line_id.container_type_id",
        store=True,
        readonly=True,
    )

    # Related field for display
    fee_type_id = fields.Many2one(
        related='fee_line_id.fee_type_id',
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ('unique_booking_line_fee', 
         'unique(booking_line_id, fee_line_id)', 
         'This fee has already been added to this booking line.')
    ]

    @api.onchange('fee_line_id')
    def _onchange_fee_line_id(self):
        if self.fee_line_id:
            self.amount = self.fee_line_id.amount

    @api.depends('fee_line_id', 'amount')
    def _compute_name(self):
        for record in self:
            if record.fee_line_id:
                fee_type_name = record.fee_line_id.fee_type_id.name or 'Fee'
                currency_name = record.fee_line_id.currency_id.name or ''
                record.name = f"{fee_type_name}: {record.amount:,.0f} {currency_name}"
            else:
                record.name = "Fee"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Set amount from fee_line if not provided
            if vals.get('fee_line_id') and not vals.get('amount'):
                fee_line = self.env['freight.purchase.fee.line'].browse(vals['fee_line_id'])
                vals['amount'] = fee_line.amount

        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals) 