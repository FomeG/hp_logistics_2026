from ..validators.booking_line_validator import BookingLineValidator
from odoo import models, fields, api, exceptions, _
from ..services.freight_purchase_booking_inventory_service import FreightPurchaseBookingInventoryService
from ..services.freight_purchase_booking_line_service import FreightPurchaseBookingLineService
from odoo.exceptions import UserError

class FreightPurchaseBookingLine(models.Model):
    _name = 'freight.purchase.booking.line'
    _description = 'Freight Booking Line'
    _inherit = ['mail.thread', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    booking_id = fields.Many2one('freight.purchase.booking', required=True, ondelete='cascade', string='Booking')
    #filter with perf reason
    pod_id = fields.Many2one(related='booking_id.quotation_id.route_id.pod_id',store=True,readonly=True,string='Port of Discharge (POD)')

    #keep ref with quotation line in order to track the price of    preorder vs order
    quotation_line_id = fields.Many2one('freight.purchase.quotation.line', required=False, string='Quotation Line', tracking=True, domain="[('quotation_id', '=', quotation_id)]")
    container_type_id = fields.Many2one(related='quotation_line_id.container_type_id',store=True,readonly=True, string='Container Type DB')

    # pre-order
    quantity = fields.Integer(string="Quantity",required=True, default=1, tracking=True)
    unit_price = fields.Float(string='Unit Price', required=True,digits="Unit price", default=1, tracking=True)
    price = fields.Float(string="Total price",compute="_compute_price", store=True, tracking=True, readonly=False)
    sale_order_line_ids = fields.One2many('sale.order.line', 'booking_line_id', string='Sale Order Lines', tracking=True)
    reserved_by_id = fields.Many2one('res.users', string='Reserved by Salesperson', compute='_compute_user_reserve', store=True)
    employee_id = fields.Many2one('hr.employee', string='Sale Members', compute='_compute_employee_id', inverse='_inverse_employee_id', store=False)

    #these fields will be used for filter
    sale_order_id = fields.Many2one('sale.order', compute='_compute_sale_info', store=True, string='Sale Order')
    customer_id = fields.Many2one('res.partner', compute='_compute_sale_info', store=True, string='Customer')
    salesman_id = fields.Many2one('res.users', compute='_compute_sale_info', store=True, string='Salesperson')

    #todo: move this to settings
    RESERVATION_DEADLINE_HOURS = 24
    reservation_expiration_date = fields.Datetime(
        string='Reservation Expiry',
        help="Date after which the reservation is released if the sale order is not confirmed."
    )

    # Computed TEU
    teu_volume = fields.Float(compute='_compute_teu_volume', store=True, string='Teu Volume')
    note = fields.Text()

    status = fields.Selection(
        string="Status",
        selection=[
            ('available', f"Available"),
            ('reserved', f"Reserved"),
            ('allocated', f"Allocated"),
            ('shipped', f"Shipped"),
            ('cancelled', f"Cancelled"),
        ],
        default='available',
        tracking=True,
        index=True,
        store=True,
    )
    # Temporary fields for quotation line creation
    quotation_line_container_type_id = fields.Many2one('container.type', store=False, string='Tempo Container Type')
    quotation_line_cost = fields.Float(string="Booking price",store=False)
    quotation_line_price = fields.Float(string="Internal price set by sale director", store=False, readonly=False)
    quotation_id = fields.Many2one('freight.purchase.quotation',related='booking_id.quotation_id',store=False,readonly=True)
    # Computed field to check if quotation lines exist
    has_quotation_lines = fields.Boolean(store=False, string='Has Quotation Lines', default=True)

    # Computed invisible btn add sale line
    can_add_sale_line = fields.Boolean(compute='_compute_can_add_sale_line', store=False)

    # Fee-related fields
    fee_line_ids = fields.One2many(
        comodel_name="freight.purchase.booking.line.fee",
        inverse_name="booking_line_id",
        string="Fee Lines"
    )

    #remind
    remind_id = fields.Many2one('freight.purchase.remind', string="Reminder")
    reminder_count = fields.Integer(string='Reminder Sent', default=0)
    remind_enabled = fields.Boolean(
        string="Enable Reminder",
        compute='_compute_remind_enabled',
        inverse='_inverse_remind_enabled',
        store=False,
        default=True
    )
    name = fields.Char(
        string="Name",
        compute='_compute_name',
        store=False
    )

    @api.depends('quotation_line_id')
    def _compute_name(self):
        for record in self:
            if record.quotation_line_id:
                record.name = f"Booking line of: {record.quotation_line_id.name}"
            else:
                record.name = ''

    @api.depends('remind_id.without_booking_line_ids')
    def _compute_remind_enabled(self):
        for line in self:
            if line.remind_id:
                line.remind_enabled = line not in line.remind_id.without_booking_line_ids
            else:
                line.remind_enabled = True

    def _inverse_remind_enabled(self):
        for line in self:
            remind = line.remind_id
            if not remind:
                if not line.remind_enabled:
                    remind = self.env['freight.purchase.remind'].search([
                        ('type', '=', 'booking_line'),
                        ('is_active', '=', True),
                    ], limit=1)
                    if not remind:
                        raise exceptions.UserError("No active booking reminder configuration found.")
                    line.remind_id = remind
                else:
                    continue

            if line.remind_enabled:
                remind.without_booking_line_ids = [(3, line.id)]
            else:
                if line not in remind.without_booking_line_ids:
                    remind.without_booking_line_ids = [(4, line.id)]
    
    @api.depends('sale_order_line_ids', 'status')
    def _compute_can_add_sale_line(self):
        for record in self:
            record.can_add_sale_line = False if record.sale_order_line_ids or record.status == 'cancelled' else True

    @api.depends('sale_order_line_ids')
    def _compute_sale_info(self):
        for line in self:
            line.sale_order_id = False
            line.customer_id = False
            line.salesman_id = False
            first_line = line.sale_order_line_ids[:1]
            if first_line:
                order = first_line.order_id
                line.sale_order_id = order.id
                line.customer_id = order.partner_id.id
                line.salesman_id = order.user_id.id

    @api.depends('container_type_id','quotation_line_container_type_id', 'quantity')
    def _compute_teu_volume(self):
        for line in self:
            teu_ratio = 0.0
            if line.container_type_id:
                teu_ratio = line.container_type_id.teu or 0.0
            elif line.quotation_line_container_type_id:
                teu_ratio = line.quotation_line_container_type_id.teu or 0.0
            line.teu_volume = teu_ratio * (line.quantity or 0)

    @api.depends('employee_id')
    def _compute_user_reserve(self):
        for line in self:
            employee = line.employee_id
            if employee and employee.user_id:
                line.reserved_by_id = employee.user_id
            else:
                line.reserved_by_id = False
    
    @api.depends('reserved_by_id')
    def _compute_employee_id(self):
        for record in self:
            user = record.reserved_by_id
            record.employee_id = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1) if user else False

    def _inverse_employee_id(self):
        for record in self:
            record.reserved_by_id = record.employee_id.user_id if record.employee_id and record.employee_id.user_id else False

    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        if self.booking_id:
            self.quotation_line_id = False
            self.quotation_line_container_type_id = False
            self.quotation_line_cost = 0
            self.quotation_line_price = 0
            self.has_quotation_lines = len(self.quotation_id.line_ids) > 0
            return {
                'domain': {
                    'quotation_line_id': [('quotation_id', '=', self.quotation_id)]
                }
            }
    #set default internal price based on cost
    @api.onchange('quotation_line_cost')
    def _onchange_quotation_line_cost(self):
        for record in self:
            if not record.quotation_line_price or record.quotation_line_price == 0.0:
                record.quotation_line_price = record.quotation_line_cost
    # unit price based on quotation price
    @api.onchange('quotation_line_id', 'quotation_line_price')
    def _onchange_set_price_unit(self):
        for record in self:
            record.unit_price = 0.0
            if record.quotation_line_id:
                record.unit_price = record.quotation_line_id.price or 0.0
            elif record.quotation_line_price:
                record.unit_price = record.quotation_line_price or 0.0

    @api.depends('quantity', 'unit_price')
    def _compute_price(self):
        for record in self:
            record.price = 0.0
            if record.quantity > 0:
                record.price = record.unit_price * record.quantity

    def write(self, vals_list):
        origin_sale_order_lines = {rec.id: rec.sale_order_line_ids.ids for rec in self}
        res = super().write(vals_list)
        if 'sale_order_line_ids' in vals_list:
            for record in self:
                record._event('on_change_sale_order_line').notify(
                    record,
                    origin_sale_order_lines[record.id],
                    record.sale_order_line_ids.ids
                )
        return res

    def action_add_sale_line(self):
        return {
            'name': 'Select Sale Order Line',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list',
            'view_id': self.env.ref('hp_freight_purchase.view_sale_order_line_selection').id,
            'target': 'new',
            'domain': [('booking_line_id', '=', False)],
            'context': {
                'booking_line_id': self.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        try:

            for vals in vals_list:
                validated, errors = BookingLineValidator.validate(vals, self.env)
                if errors:
                    raise exceptions.ValidationError("\n".join([f"• {e}" for e in errors]))
                if not vals.get('quotation_line_id'):
                    try:
                        quotation_line = self.env['freight.purchase.quotation.line'].create_from_booking_line_form(vals)
                        vals['quotation_line_id'] = quotation_line.id
                    except exceptions.ValidationError as e:
                        # This will show as a nice user error in the UI
                        raise exceptions.ValidationError(f"Cannot create quotation line:\n{e}")
                    except Exception as e:
                        raise exceptions.ValidationError("A system error occurred while creating the quotation line.")

            return super().create(vals_list)
        except exceptions.ValidationError:
            raise
        except Exception as e:
            raise exceptions.ValidationError("An unexpected error occurred. Please try again or contact support.")

    def write(self, vals):
        for record in self:
            if record.status == 'cancel':
                raise exceptions.UserError("You cannot update booking line that is in 'Cancelled' status.")

        if 'status' in vals and len(self) == 1:
            ctx = dict(self.env.context)
            ctx['old_status'] = self.status
            return super(FreightPurchaseBookingLine, self.with_context(ctx)).write(vals)

        return super().write(vals)


    @api.constrains('booking_id', 'container_type_id', 'quantity')
    def _check_quantity_against_quotation(self):
        for line in self:
            if line.booking_id and line.container_type_id and line.quantity:
                container_avaliable = FreightPurchaseBookingInventoryService(
                    self.env).count_quantity_container_available_in_booking(line.booking_id.id,
                                                                            line.container_type_id.id)
                if line.quantity > container_avaliable:
                    raise exceptions.ValidationError(
                        f"Total quantity must be less than or equal to {container_avaliable}."
                    )

    def _reservation_expiration_reminder(self):
        service = FreightPurchaseBookingLineService(self.env)
        service.reservation_expiration_reminder()