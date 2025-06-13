from odoo import models, fields


class FreightPurchaseBookingLineHistory(models.Model):
    _name = 'freight.purchase.booking.line.history'
    _description = 'Booking Line History'

    booking_line_id = fields.Many2one('freight.purchase.booking.line', required=True, ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    event_type = fields.Selection([
        ('assign', 'Assigned'),
        ('unassign', 'Unassigned'),
        ('expired', 'Expired Automatically'),
        ('manual_expire', 'Unassigned Manually'),
    ], required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    timestamp = fields.Datetime(default=fields.Datetime.now)
    note = fields.Text()
