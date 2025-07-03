from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.booking_inventory_validator import BookingInventoryValidator

class FreightPurchaseBookingInventory(models.Model):
    _name = 'freight.purchase.booking.inventory'
    _description = 'Booking - Container Relation'

    ACTION_IN = 'in'
    ACTION_OUT = 'out'
    ACTION_RETURN = 'return'

    booking_id = fields.Many2one('freight.purchase.booking', required=True, string='Booking')
    booking_line_id = fields.Many2one('freight.purchase.booking.line', string='Booking Line')
    container_type_id = fields.Many2one('container.type', required=True, string='Container Type')
    quantity = fields.Integer(string='Quantity', required=True, default=1)
    action = fields.Selection(
        string="Action",
        selection=[
            ('in', f'Inbound'),
            ('out', f'Outbound'),
            ('return', f'Return'),
        ],
        default='in',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = BookingInventoryValidator.validate_create(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)