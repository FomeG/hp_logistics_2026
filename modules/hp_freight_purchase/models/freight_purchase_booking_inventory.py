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

    allow_container_type_ids = fields.Many2many(
        comodel_name='container.type',
        compute='_compute_allow_container_type_ids',
        store=False,ondelete = "cascade",
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
        records = super().create(vals_list)
        for record in records:
            booking = record.booking_id
            if (
                booking
                and booking.booking_mode == 'without_quotation'
                and booking.quotation_id
            ):
                quotation = booking.quotation_id
                quotation_line_model = self.env['freight.purchase.quotation.line']

                quotation_line_model.create({
                    'quotation_id': quotation.id,
                    'container_type_id': record.container_type_id.id,
                    'price':1,
                    'cost': 2,
                    # Có thể thêm các field khác nếu cần:
                    # 'action': record.action,
                    # 'booking_line_id': record.booking_line_id.id,
                })
                _logger.info(f"[AUTO] Created quotation line for container {record.container_type_id.display_name}")

        return records
    @api.depends('booking_id.quotation_id.line_ids.container_type_id', 'booking_id.booking_mode')
    def _compute_allow_container_type_ids(self):
        for rec in self:
            if not rec.booking_id or not rec.booking_id.quotation_id:
                rec.allow_container_type_ids = False
            elif rec.booking_id.booking_mode == 'with_quotation':
                # Original logic: Only allow container types from quotation lines
                rec.allow_container_type_ids = rec.booking_id.quotation_id.line_ids.mapped('container_type_id')
            elif rec.booking_id.booking_mode == 'without_quotation':
                # New logic: Allow all container types (no restriction)
                rec.allow_container_type_ids = self.env['container.type'].search([])
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
