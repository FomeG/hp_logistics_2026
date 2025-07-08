from pkg_resources import require
from odoo import models, fields, api
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
from odoo.exceptions import ValidationError
from ..validators.booking_validator import BookingCreateValidator, BookingUpdateValidator
from collections import defaultdict
from odoo.addons.hp_freight_purchase.services.freight_purchase_booking_inventory_service import FreightPurchaseBookingInventoryService

class FreightPurchaseBooking(models.Model):

    _name = 'freight.purchase.booking'
    _description = 'Freight Purchase Booking'
    _inherit = ['mail.thread','unique.code.mixin', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Booking Name',
        # compute='_compute_name',
        store=True,
        required=True,
        tracking=True
    )
    vessel_id = fields.Many2one('freight.purchase.vessel', string="Vessel",required=True,  tracking=True)
    quotation_id = fields.Many2one('freight.purchase.quotation',required=True, string="Quotation",  tracking=True)
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
    #duplication for the perf reason
    route_id = fields.Many2one(
        related='quotation_id.route_id',
        store=True
    )
    pol_id = fields.Many2one(
        related='route_id.pol_id',
        store=True
    )
    pod_id = fields.Many2one(
        related='route_id.pod_id',
        store=True
    )
    direction = fields.Selection(
        related='route_id.direction',
        store=True
    )
    shipping_line_id = fields.Many2one(related='quotation_id.shipping_line_id', store=True)
    teu_volume = fields.Float()
    note = fields.Text()
    line_ids = fields.One2many('freight.purchase.booking.line', 'booking_id', string='Booking Lines')
    booking_mode = fields.Selection([
        ('with_quotation', 'With Quotation'),
        ('without_quotation', 'Without Quotation'),
    ], string='Booking Mode', required=True, default='with_quotation')

    # Temporary fields for quotation creation
    quotation_route_id = fields.Many2one('freight.purchase.route',string='Tempo Route',store=False)
    quotation_shipping_line_id = fields.Many2one('res.partner',string="Shipping line", domain="[('is_shipping_line', '=', True)]", store=False)

    total_booking_lines = fields.Char(string="Total Booking Lines", compute='_compute_total_booking_lines', store=False)

    # inventory transaction
    booking_inventory_ids = fields.One2many(
        'freight.purchase.booking.inventory',
        'booking_id', 
        string='Booking Inventories'
    )
    is_show_inventory = fields.Boolean(compute='_compute_is_show_inventory', store=False)

    @api.onchange('booking_mode')
    def _onchange_booking_mode(self):
        for record in self:
            if record.booking_mode == 'without_quotation':
                record.quotation_id = False

    @api.model_create_multi
    def create(self, vals_list: list[ValuesType]) -> Self:
        for vals in vals_list:
            validated, errors = BookingCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        
            if vals.get('booking_mode') == 'without_quotation':
                # If booking without quotation → create a quotation
                quotation = self.env['freight.purchase.quotation'].create_from_booking_form(vals)
                vals['quotation_id'] = quotation.id

                # Prepare name using temporary fields
                shipping_name = ''
                route_name = ''
                etd_str = ''

                if vals.get('quotation_shipping_line_id'):
                    shipping_name = self.env['res.partner'].browse(vals.get('quotation_shipping_line_id')).name or ''
                if vals.get('quotation_route_id'):
                    route_name = self.env['freight.purchase.route'].browse(vals.get('quotation_route_id')).name or ''
                if vals.get('etd'):
                    etd_str = fields.Date.to_date(vals['etd']).strftime('%d-%m-%Y')

                print(f"quotation_shipping_line_id: {shipping_name}")
                print(f"quotation_route_id: {route_name}")
                print(f"etd: {etd_str}")

                if shipping_name and route_name and etd_str:
                    vals['name'] = f"Booking - {shipping_name} - {route_name} - {etd_str}"
                else:
                    vals['name'] = False  # Leave empty if not enough info

                print(f"name: {vals['name']}")

            else:
                # Booking with quotation → use related quotation fields
                shipping_name = ''
                route_name = ''
                etd_str = ''

                if vals.get('quotation_id'):
                    quotation = self.env['freight.purchase.quotation'].browse(vals['quotation_id'])
                    shipping_name = quotation.shipping_line_id.name or ''
                    route_name = quotation.route_id.name or ''
                if vals.get('etd'):
                    etd_str = fields.Date.to_date(vals['etd']).strftime('%d-%m-%Y')

                if shipping_name and route_name and etd_str:
                    vals['name'] = f"Booking - {shipping_name} - {route_name} - {etd_str}"
                else:
                    vals['name'] = False  # Leave empty if not enough info

        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            validated, errors = BookingUpdateValidator.validate(vals, self.env, record.id)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))

            if 'booking_mode' in vals and record.booking_mode != vals['booking_mode']:
                raise UserError("You cannot change the booking mode after creation.")
            
            if 'line_ids' in vals and record.quotation_id:
                container_qty_map = defaultdict(int)
                for line in vals['line_ids']:
                    if line[0] == 0:
                        data = line[2]
                        if data.get('status') == 'cancel':
                            continue

                        quantity = data.get('quantity', 0)
                        container_id = data.get('container_type_id')
                        if not container_id:
                            quotation_line = self.env['freight.purchase.quotation.line'].sudo().browse(data.get('quotation_line_id'))
                            container_id = quotation_line.container_type_id.id
                                
                        container_qty_map[container_id] += quantity

                for container_id, added_qty in container_qty_map.items():
                    container_avaliable = FreightPurchaseBookingInventoryService(self.env).count_quantity_container_available_in_booking(record.id, container_id)
                    if added_qty > container_avaliable:
                        container = self.env['container.type'].sudo().browse(container_id)
                        raise ValidationError(f"Total quantity of container {container.name} must be less than or equal to {container_avaliable}.")

        return super().write(vals)

    # For making the name updated visibly
    @api.onchange('shipping_line_id.name', 'route_id.name', 'etd', 'quotation_route_id.name',
                 'quotation_shipping_line_id.name', 'booking_mode')
    def _compute_name(self):
        for record in self:
            if record.booking_mode == 'with_quotation':
                # With quotation: use related shipping_line_id and route_id
                if record.shipping_line_id and record.route_id and record.etd:
                    shipping_name = record.shipping_line_id.name or ''
                    route_name = record.route_id.name or ''
                    formatted_date = ''

                    if isinstance(record.etd, (date, datetime)):
                        formatted_date = record.etd.strftime('%d-%m-%Y')

                    record.name = f"Booking - {shipping_name} - {route_name} - {formatted_date}"
                else:
                    record.name = False  # Leave empty if missing data

            elif record.booking_mode == 'without_quotation':
                # Without quotation: use temporary fields quotation_shipping_line_id and quotation_route_id
                if record.quotation_shipping_line_id and record.quotation_route_id and record.etd:
                    shipping_name = record.quotation_shipping_line_id.name or ''
                    route_name = record.quotation_route_id.name or ''
                    formatted_date = ''

                    if isinstance(record.etd, (date, datetime)):
                        formatted_date = record.etd.strftime('%d-%m-%Y')

                    record.name = f"Booking - {shipping_name} - {route_name} - {formatted_date}"
                else:
                    record.name = False  # Leave empty if missing data
            else:
                record.name = False  # Fallback, though not expected

    @api.depends('line_ids')
    def _compute_total_booking_lines(self):
        for record in self:
            record.total_booking_lines = "0 Booking Line(s)"
            if record.line_ids:
                record.total_booking_lines = f"{len(record.line_ids)} Booking Line(s)"
    
    @api.depends('quotation_id')
    def _compute_is_show_inventory(self):
        for record in self:
            record.is_show_inventory = True if record.id and record.quotation_id.line_ids else False