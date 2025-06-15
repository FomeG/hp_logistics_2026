from odoo import models, fields


class FreightPurchaseBookingLineHistory(models.Model):
    _name = 'freight.purchase.booking.line.history'
    _description = 'Booking Line History'
    _inherit = ['mail.thread']

    booking_line_id = fields.Many2one('freight.purchase.booking.line', required=True, ondelete='cascade')
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    event_type = fields.Selection([
        ('assign', 'Assigned'),
        ('unassign', 'Unassigned'),
        ('expired', 'Expired Automatically'),
        ('manual_expire', 'Unassigned Manually'),
    ], required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    note = fields.Text()
