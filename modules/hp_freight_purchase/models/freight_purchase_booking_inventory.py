from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.booking_inventory_validator import BookingInventoryValidator
import logging

_logger = logging.getLogger(__name__)

class FreightPurchaseBookingInventory(models.Model):
    _name = 'freight.purchase.booking.inventory'
    _description = 'Booking - Container Relation'

    ACTION_IN = 'in'
    ACTION_OUT = 'out'
    ACTION_RETURN = 'return'

    booking_id = fields.Many2one('freight.purchase.booking', required=True, string='Booking',ondelete = "cascade",)
    booking_line_id = fields.Many2one('freight.purchase.booking.line', string='Booking Line',ondelete = "cascade",)
    container_type_id = fields.Many2one('container.type', required=True, string='Container Type',ondelete = "cascade",)
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

    str_inventory_booking_line = fields.Char(
        string='Str Inventory Booking Line',
        compute='_compute_inventory_booking_line',
        store=False
    )

    tempo_container_price = fields.Float(
        string='price',
        store=False,
    )
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = BookingInventoryValidator.validate_create(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        records = super().create(vals_list)
        records._notify_booking_inventory_created(vals_list)
        return records

    def _compute_inventory_booking_line(self):
        for rec in self:
            if rec.booking_line_id and rec.booking_line_id.salesman_id:
                rec.str_inventory_booking_line = rec.booking_line_id.salesman_id.name
            elif rec.booking_line_id:
                rec.str_inventory_booking_line = f"Booking Line #{rec.booking_line_id.id}"
            else:
                rec.str_inventory_booking_line = False

    def _notify_booking_inventory_created(self, booking_inventory_form):
        for i, record in enumerate(self):
            self._event('on_booking_inventory_create').notify(
                record=record,
                booking_inventory_form=booking_inventory_form[i],
            )
