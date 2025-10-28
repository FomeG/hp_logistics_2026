from pkg_resources import require
from odoo import models, fields, api
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
from odoo.exceptions import ValidationError
from .freight_purchase_booking_inventory import FreightPurchaseBookingInventory
from ..validators.booking_validator import BookingCreateValidator, BookingUpdateValidator
from collections import defaultdict
from ..services.freight_purchase_booking_inventory_service import FreightPurchaseBookingInventoryService
from ..services.freight_purchase_quotation_service import FreightPurchaseQuotationService
from ..services.freight_purchase_booking_line_service import FreightPurchaseBookingLineService
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
    quotation_id = fields.Many2one(
        'freight.purchase.quotation',
        required=False,
        string="Quotation",
        tracking=True,
        ondelete = "cascade"
    )
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
    route_transit_id = fields.Many2one(
        'freight.purchase.route',
        related = 'quotation_id.route_transit_id',
        string = "Route transit"
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
    quotation_shipping_line_id = fields.Many2one('res.partner',string="Shipping line", domain="[('partner_main_type_id.code', '=', 'shipping_line')]", store=False)

    total_booking_lines = fields.Char(string="Total Booking Lines", compute='_compute_total_booking_lines', store=False)

    # inventory transaction
    booking_inventory_ids = fields.One2many(
        'freight.purchase.booking.inventory',
        'booking_id', 
        string='Booking Inventories',
        ondelete = "cascade",
    )
    is_show_inventory = fields.Boolean(compute='_compute_is_show_inventory', store=False)
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
        ondelete = "cascade",

    )
    has_fees = fields.Boolean(
        compute='_compute_has_fees',
        store=False,
        string="Has Fees"
    )
    can_apply_fees = fields.Boolean(
        compute='_compute_can_apply_fees',
        store=False,
        string="Can Apply Fees"
    )

    @api.onchange('booking_mode')
    def _onchange_booking_mode(self):
        for record in self:
            if record.booking_mode == 'without_quotation':
                record.quotation_id = False
    #to remove later
        # Skip validation if creating automatically
        # if not self.env.context.get('skip_validator'):
        #     validated, errors = BookingCreateValidator.validate(vals, self.env)
        #     if errors:
        #         raise ValidationError("\n".join([f"• {e}" for e in errors]))
        #
        # if vals.get('booking_mode') == 'without_quotation':
        # If booking without quotation → create a quotation

        # Prepare name using temporary fields
        # shipping_name = ''
        # route_name = ''
        # etd_str = ''
        #
        # if vals.get('quotation_shipping_line_id'):
        #     shipping_name = self.env['res.partner'].browse(vals.get('quotation_shipping_line_id')).name or ''
        # if vals.get('quotation_route_id'):
        #     route_name = self.env['freight.purchase.route'].browse(vals.get('quotation_route_id')).name or ''
        # if vals.get('etd'):
        #     etd_str = fields.Date.to_date(vals['etd']).strftime('%d-%m-%Y')
        #
        # if shipping_name and route_name and etd_str:
        #     vals['name'] = f"Booking - {shipping_name} - {route_name} - {etd_str}"
        # else:
        #     vals['name'] = False  # Leave empty if not enough info

        # else:
        #     # Booking with quotation → use related quotation fields
        #     shipping_name = ''
        #     route_name = ''
        #     etd_str = ''
        #
        #     if vals.get('quotation_id'):
        #         quotation = self.env['freight.purchase.quotation'].browse(vals['quotation_id'])
        #         shipping_name = quotation.shipping_line_id.name or ''
        #         route_name = quotation.route_id.name or ''
        #     if vals.get('etd'):
        #         etd_str = fields.Date.to_date(vals['etd']).strftime('%d-%m-%Y')
    # if shipping_name and route_name and etd_str:
    #     vals['name'] = f"Booking - {shipping_name} - {route_name} - {etd_str}"
    # else:
    #     vals['name'] = False  # Leave empty if not enough info

    # self._event('on_booking_without_quotation_created').notify(
    #     record=self,
    #     route_id=booking_form.get('quotation_route_id'),
    # 'shipping_line_id': booking_form.get('quotation_shipping_line_id'),
    # 'available_from': fields.Date.today(),
    # 'available_to': booking_form.get('etd'),
    # )

    # project_task_id = self._context.get('default_project_task_id')
    # if project_task_id:
    #     project_task = self.env['project.task'].browse(project_task_id)
    #     if project_task.exists():
    #         booking = records[0]
    #         booking_line = FreightPurchaseBookingLineService(self.env).create_booking_line_by_task(project_task, booking.id)
    #         if booking_line:
    #             project_task.booking_id = records[0].id

    @api.model_create_multi
    def create(self, vals_list: list[ValuesType]) -> Self:
        for vals in vals_list:
            today = fields.Date.today().strftime('%Y%m%d')
            seq_number = self.env['ir.sequence'].next_by_code('freight.purchase.booking')
            vals['name'] = f"Booking/{today}/{seq_number}"
        records = super().create(vals_list)
        records._notify_booking_created(vals_list)
        return records

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
                        if container_avaliable == 0:
                            raise ValidationError(
                                f"No available inventory for container {container.name}. Please check the booking inventory."
                            )
                        else:
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

    @api.depends('quotation_id', 'booking_mode')
    def _compute_is_show_inventory(self):
        for record in self:
            if not record.id:
                record.is_show_inventory = False
            elif record.booking_mode == 'with_quotation':
                record.is_show_inventory = bool(record.quotation_id and record.quotation_id.line_ids)
            elif record.booking_mode == 'without_quotation' and record.id and record.quotation_id:
                record.is_show_inventory = True
            else:
                record.is_show_inventory = False

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

    @api.depends('has_fees', 'has_inventory', 'quotation_id', 'line_ids')
    def _compute_can_apply_fees(self):
        for record in self:
            # Can apply fees if: has quotation with fees (always show button for better UX)
            has_quotation_fees = (
                record.quotation_id and 
                (len(record.quotation_id.fee_ids) > 0 or 
                 any(len(line.fee_line_ids) > 0 for line in record.quotation_id.line_ids))
            )

            _logger.info(f"common quotation fee: {len(record.quotation_id.fee_ids)}")
            _logger.info(f"specific quotation fee: {any(len(line.fee_line_ids) > 0 for line in record.quotation_id.line_ids)}")
            
            record.can_apply_fees = has_quotation_fees

    def action_apply_fees_from_quotation(self):
        """Apply fees from quotation to booking"""
        try:
            service = FreightPurchaseQuotationService(self.env)
            result = service.apply_fees_from_quotation_to_booking(self)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success' if result['type'] == 'success' else 'Warning',
                    'message': result['message'],
                    'type': result['type'],
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    # handel context from task
    @api.onchange('quotation_id')
    def _onchange_quotation_id(self):
        for line in self:
            default_id = self.env.context.get('default_quotation_id')
            if default_id and line.quotation_id and line.quotation_id.id != default_id:
                raise ValidationError('You can only select the quotation passed from the quotation context')

    has_booking_id = fields.Boolean(
        compute='_compute_has_booking_id',
        store=False
    )

    def _compute_has_booking_id(self):
        for record in self:
            # Nếu record đã lưu thì record.id khác False
            record.has_booking_id = bool(record.id)

    def _notify_booking_created(self, booking_form):
        for i, record in enumerate(self):
            self._event('on_booking_created').notify(
                record=record,
                booking_form=booking_form[i],
            )
    def create_quotation(self, booking_form):
        QuotationModel = self.env['freight.purchase.quotation']
        for record in self:
            try:
                quotation = QuotationModel.create({
                    'route_id': booking_form['quotation_route_id'],
                    'shipping_line_id': booking_form['quotation_shipping_line_id'],
                    'available_from': fields.Date.today(),
                    'available_to': booking_form['etd'],
                    'is_active': True
                })
                record.quotation_id = quotation.id
            except Exception as e:
                _logger.error("Error in create_quotation: %s", str(e))
