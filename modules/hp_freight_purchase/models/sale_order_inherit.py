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

        sale_order_from_location_id = self.from_location_id.id
        sale_order_to_location_id = self.to_location_id.id
        domain = [
            ('sale_order_id', '=', False),
            ('booking_id.quotation_id.from_location_id', '=', sale_order_from_location_id),
            ('booking_id.quotation_id.to_location_id', '=', sale_order_to_location_id),
        ]

        if self.container_type_id:
            domain.append(('container_type_id', '=',self.container_type_id.id))

        return {
            'name': 'Select Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.booking.line',
            'view_mode': 'list',
            'views': [(self.env.ref('hp_freight_purchase.assign_booking_line_list_view').id, 'list')],
            'domain': domain, 
            'target': 'new',
            'context': {
                'sale_order_id': self.id,
            },
        }