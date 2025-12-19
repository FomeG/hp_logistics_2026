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
        string='Str Inventory Booking Line',
        compute='_compute_inventory_booking_line',
        store=False
    )

    tempo_container_price = fields.Float(
        string='price',
        store=False,
    )
    #todo: invisibility should depends on booking mode, quotation line and container
    can_create_quotation_line = fields.Boolean(
        store=False,
        compute='_compute_can_create_quotation_line',
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
    
    @api.depends('booking_id.quotation_id.line_ids.container_type_id', 'booking_id.booking_mode')
    def _compute_allow_container_type_ids(self):
        for rec in self:
            if not rec.booking_id or not rec.booking_id.quotation_id:
                rec.allow_container_type_ids = False
            elif rec.booking_id.quotation_id.line_ids:
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

    @api.depends('booking_id.quotation_id.line_ids')
    def _compute_can_create_quotation_line(self):
        for rec in self:
            rec.can_create_quotation_line = rec.booking_id.quotation_id and not rec.booking_id.quotation_id.line_ids

    def _notify_booking_inventory_created(self, booking_inventory_form):
        for i, record in enumerate(self):
            self._event('on_booking_inventory_create').notify(
                record=record,
                booking_inventory_form=booking_inventory_form[i],
            )

    def create_quotation_line(self, booking_inventory_form):
        if 'tempo_container_price' not in booking_inventory_form:
            return False
        QuotationLineModel = self.env['freight.purchase.quotation.line']
        for record in self:
            try:
                quotation_id = record.booking_id.quotation_id.id
                container_id = record.container_type_id.id
                price = booking_inventory_form['tempo_container_price']
                quotation_line = QuotationLineModel.search([
                    ('quotation_id', '=', quotation_id),
                    ('container_type_id', '=', container_id),
                ])
                if quotation_line:
                    _logger.info('ALREADY HAVING QUOTATION LINES')
                    continue
                QuotationLineModel.create({
                    'quotation_id': quotation_id,
                    'container_type_id': container_id,
                    'cost': price,
                    'price': price
                })
            except Exception as e:
                _logger.error("Error in create_quotation_line: %s", str(e))
