# from pkg_resources import require
from odoo import models, fields, api
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
from odoo.exceptions import ValidationError
from .freight_purchase_booking_inventory import FreightPurchaseBookingInventory
from ..validators.booking_validator import BookingCreateValidator, BookingUpdateValidator
from collections import defaultdict
from ..services.freight_purchase_booking_inventory_service import FreightPurchaseBookingInventoryService
from ..services.freight_purchase_booking_line_service import FreightPurchaseBookingLineService
from ...hp_components.models import constants
import logging

_logger = logging.getLogger(__name__)

class FreightPurchaseBooking(models.Model):

    _name = 'freight.purchase.booking'
    _description = 'Freight Purchase Booking'
    _inherit = ['mail.thread','unique.code.mixin', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Booking Name',
        compute='_compute_name',
        store=True,
        required=True,
        tracking=True
    )
    vessel_id = fields.Many2one('freight.purchase.vessel', string="Vessel",required=True,  tracking=True)
    voyage = fields.Char(
        string="Voyage",
        required=True,
        tracking=True,
    ) # need to recheck, maybe many2one to voyage model, 1 voyage can have many booking

    etd = fields.Date(required=True, index=True,  tracking=True)
    status = fields.Selection(
        string="Status",
        selection=[
            ('draft', f'Draft'),
            ('pending', f'Pending'),
            ('confirmed', f'Confirmed'),
            ('fully_assigned', f'Fully Assigned'),
            ('shipped', f'Shipped'),
            ('cancelled', f'Cancelled'),
            ('expired', f'Expired'),
        ],
        default='confirmed',
        tracking=True,
        index=True,
        store=True,
    )

    from_location_id = fields.Many2one(
        string="POL",
        comodel_name='location.base',
        tracking=True,
    )
    to_location_id = fields.Many2one(
        string="POD",
        comodel_name='location.base',
        tracking=True,
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipping Line',
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        tracking=True,
    )
    teu_volume = fields.Float()
    note = fields.Text()
    line_ids = fields.One2many(
        comodel_name='freight.purchase.booking.line',
        inverse_name='booking_id',
        string='Booking Lines',
        ondelete = "cascade",
    )

    total_booking_lines = fields.Char(string="Total Booking Lines", compute='_compute_total_booking_lines', store=False)

    # inventory transaction
    booking_inventory_ids = fields.One2many(
        'freight.purchase.booking.inventory',
        'booking_id', 
        string='Booking Inventories',
        # ondelete = "cascade",
    )

    has_inventory = fields.Boolean(
        compute='_compute_has_inventory',
        store=False
    )
    inventory_summary = fields.Text(
        compute='_compute_inventory_summary',
        string="Container Inventory Summary",
        store=False
    )

    # Fee-related fields
    fee_ids = fields.One2many(
        comodel_name="freight.purchase.booking.fee",
        inverse_name="booking_id",
        string="Common Fees",
        # ondelete = "cascade",
    )
    has_fees = fields.Boolean(
        compute='_compute_has_fees',
        store=False,
        string="Has Fees"
    )
    # Documents
    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='booking_id',
        string='Documents'
    )

    _sql_constraints = [
        ('vessel_voyage_unique', 'unique(vessel_id,voyage)', 'The voyage and vessel must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list: list[ValuesType]) -> Self:
        for vals in vals_list:
            validated, errors = BookingCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))

            today = fields.Date.today().strftime('%Y%m%d')
            seq_number = self.env['ir.sequence'].next_by_code('freight.purchase.booking')
            vals['name'] = f"Booking/{today}/{seq_number}"
        records = super().create(vals_list)
        return records

    def write(self, vals):
        for record in self:
            validated, errors = BookingUpdateValidator.validate(vals, self.env, record.id)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            #todo: tmp disable container inventory check
            # if 'line_ids' in vals and record.quotation_id:
            #     container_qty_map = defaultdict(int)
            #     for line in vals['line_ids']:
            #         if line[0] == 0:
            #             data = line[2]
            #             if data.get('status') == 'cancel':
            #                 continue
            #
            #             quantity = data.get('quantity', 0)
            #             container_id = data.get('container_type_id')
            #             if not container_id:
            #                 quotation_line = self.env['freight.purchase.quotation.line'].sudo().browse(data.get('quotation_line_id'))
            #                 container_id = quotation_line.container_type_id.id
            #
            #             container_qty_map[container_id] += quantity
            #
            #     for container_id, added_qty in container_qty_map.items():
            #         container_avaliable = FreightPurchaseBookingInventoryService(self.env).count_quantity_container_available_in_booking(record.id, container_id)
            #         if added_qty > container_avaliable:
            #             container = self.env['container.type'].sudo().browse(container_id)
            #             if container_avaliable == 0:
            #                 raise ValidationError(
            #                     f"No available inventory for container {container.name}. Please check the booking inventory."
            #                 )
            #             else:
            #                  raise ValidationError(f"Total quantity of container {container.name} must be less than or equal to {container_avaliable}.")
        return super().write(vals)

    @api.depends('line_ids')
    def _compute_total_booking_lines(self):
        for record in self:
            record.total_booking_lines = "0 Booking Line(s)"
            if record.line_ids:
                record.total_booking_lines = f"{len(record.line_ids)} Booking Line(s)"

    @api.depends('booking_inventory_ids')
    def _compute_has_inventory(self):
        for record in self:
            # True nếu có ít nhất 1 inventory đã được lưu (có id)
            record.has_inventory = any(inv.id for inv in record.booking_inventory_ids)

    @api.depends('booking_inventory_ids')
    def _compute_inventory_summary(self):
        for booking in self:
            summary = defaultdict(int)

            for line in booking.booking_inventory_ids:
                qty = line.quantity or 0
                if line.action in (FreightPurchaseBookingInventory.ACTION_IN, FreightPurchaseBookingInventory.ACTION_RETURN):
                    summary[line.container_type_id.name] += qty
                elif line.action == FreightPurchaseBookingInventory.ACTION_OUT:
                    summary[line.container_type_id.name] -= qty

            booking.inventory_summary = '\n'.join(f"{ct}: {qty}" for ct, qty in summary.items()) if summary else f"No inventory"

    @api.depends('fee_ids')
    def _compute_has_fees(self):
        for record in self:
            record.has_fees = len(record.fee_ids) > 0

    has_booking_id = fields.Boolean(
        compute='_compute_has_booking_id',
        store=False
    )

    def _compute_has_booking_id(self):
        for record in self:
            # Nếu record đã lưu thì record.id khác False
            record.has_booking_id = bool(record.id)
