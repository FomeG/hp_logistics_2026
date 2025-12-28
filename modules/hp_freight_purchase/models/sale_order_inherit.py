from odoo import models, fields, _
from odoo.exceptions import ValidationError

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    booking_line_id = fields.Many2one(
        comodel_name= 'freight.purchase.booking.line',
        string='Booking Line id',
        index=True,
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        related='booking_line_id.booking_id',
        readonly=True,
        index=True,
        store=False,
    )
    booking_code = fields.Char(
        string='Booking Code',
        related='booking_id.code',
        readonly=True,
        store=False,
    )

    def action_assign_booking(self):
        self.ensure_one()
        booking_line_id = self.env.context.get('booking_line_id')
        if not booking_line_id:
            raise ValidationError(_("Không tìm thấy booking_line_id trong context."))

        booking_line = self.env['freight.purchase.booking.line'].browse(booking_line_id)
        if not booking_line.exists():
            raise ValidationError(_("Booking Line với ID %s không tồn tại.") % booking_line_id)

        booking_line.sudo().sale_order_id = self.id
        self.sudo().booking_line_id = booking_line.id

        return True