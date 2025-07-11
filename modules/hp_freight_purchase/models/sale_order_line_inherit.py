from odoo import models, fields, _
from datetime import date


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    _order = 'create_date desc'

    booking_line_id = fields.Many2one('freight.purchase.booking.line')

    freight_booking_id = fields.Many2one(
        'freight.purchase.booking',
        string='Booking',
        domain="[('etd', '>', '{}')]".format(date.today()),
        tracking=True
    )

    freight_quotation_id = fields.Many2one(
        'freight.purchase.quotation',
        # domain=lambda self: self._get_freight_quotation_domain_lambda(),
        string="Freight Quotation",
        tracking=True
    )

    def action_select_this_line(self):
        booking_line_id = self.env.context.get('booking_line_id')
        if booking_line_id:
            self.write({'booking_line_id': booking_line_id})
        return {'type': 'ir.actions.act_window_close'}

    def action_create_route(self):
        """Open wizard to collect Port/Route information"""
        return {
            'name': _('Create Port/Route Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'port.route.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.order_id.id}
        }