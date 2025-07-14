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

    allow_container_type_ids = fields.Many2many(
        comodel_name='container.type',
        compute='_compute_allow_container_type_ids',
        store=False
    )

    str_inventory_booking_line = fields.Char(
        string='Booking Line',
        compute='_compute_inventory_booking_line',
        store=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = BookingInventoryValidator.validate_create(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)
    
    @api.depends('booking_id.quotation_id.line_ids.container_type_id')
    def _compute_allow_container_type_ids(self):
        for rec in self:
            if rec.booking_id and rec.booking_id.quotation_id:
                rec.allow_container_type_ids = rec.booking_id.quotation_id.line_ids.mapped('container_type_id')
            else:
                rec.allow_container_type_ids = False

    def _compute_inventory_booking_line(self):
        for rec in self:
            if rec.booking_line_id and rec.booking_line_id.salesman_id:
                rec.str_inventory_booking_line = rec.booking_line_id.salesman_id.name
            elif rec.booking_line_id:
                rec.str_inventory_booking_line = f"Booking Line #{rec.booking_line_id.id}"
            else:
                rec.str_inventory_booking_line = False
