from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PricingBooking(models.Model):
    _name = 'pricing.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Booking'
    _rec_name = 'booking_no'
    _order = 'write_date desc'

    booking_no = fields.Char(string='Booking No', tracking=True)
    voyage_id = fields.Many2one(
        'pricing.voyage', string="Tàu và số hiệu chuyến",
        tracking=True
    )
    etd = fields.Date(
        string="Estimate Departure",
        related='voyage_id.etd'
    )
    volume_quantity_1 = fields.Integer(string='Container Quantity 1', default=1, tracking=True)
    volume_cont_1 = fields.Selection(selection=[
        ('20DC', '20DC'),
        ('20RF', '20RF'),
        ('20OT', '20OT'),
        ('20HC', '20HC'),
        ('40DC', '40DC'),
        ('40HC', '40HC'),
        ('40HQ', '40HQ'),
        ('40RF', '40RF'),
        ('40HCRF', '40HCRF'),
        ('40OT', '40OT'),
    ], string='Container Type 1', default='40HC', tracking=True)
    volume_quantity_2 = fields.Integer(string='Container Quantity 2', default=0, tracking=True)
    volume_cont_2 = fields.Selection(selection=[
        ('20DC', '20DC'),
        ('20RF', '20RF'),
        ('20OT', '20OT'),
        ('20HC', '20HC'),
        ('40DC', '40DC'),
        ('40HC', '40HC'),
        ('40HQ', '40HQ'),
        ('40RF', '40RF'),
        ('40HCRF', '40HCRF'),
        ('40OT', '40OT'),
    ], string='Container Type 2', default='40HC', tracking=True)
    volume_total = fields.Integer(string='Total Volume (TEU)', compute='_compute_volume_total', store=True)
    booking_price = fields.Float('Booking Price', tracking=True)
    company_booking_price = fields.Float('Company Booking Price', tracking=True)
    booking_status = fields.Selection(selection=[
        ('booked', 'Booked'),
        ('request', 'Request'),
        ('cancel', 'Cancel'),
        ('available', 'Available'),
    ], string='Booking Status', default='available', tracking=True)

    fee_type = fields.Selection(selection=[
        ('SBJ', 'SBJ'),
        ('Allin', 'Allin'),
    ], string='Booking Fee Type', default='Allin', tracking=True)

    pricing_quotation_id = fields.Many2one(
        'pricing.quotation',
        string="Pricing Quotation"
    )

    active = fields.Boolean(default=True)

    # One2many field to see all sales order lines using this booking
    sale_line_ids = fields.One2many(
        'sale.order.line',
        'booking_id',
        string="Sales Order Lines",
        copy=False
    )

    # Computed fields for TEU tracking
    reserved_teu = fields.Float(
        string="Reserved TEU",
        compute="_compute_teu_usage",
        store=True,
        help="Total TEU reserved by sale order lines in state 'sale'"
    )

    remaining_teu = fields.Float(
        string="Remaining TEU",
        compute="_compute_teu_usage",
        store=True,
        help="Remaining TEU available for booking"
    )

    teu_warning_message = fields.Html(
        string="TEU Usage Warning",
        compute="_compute_teu_warning",
        store=False
    )

    def _validate_booking_prices(self, booking_price, company_booking_price, action=""):
        if booking_price is None or company_booking_price is None:
            raise ValidationError(f"Both Booking Price and Company Booking Price are required when {action}.")

        if booking_price <= 0 or company_booking_price <= 0:
            raise ValidationError(f"Both Booking Price and Company Booking Price must be greater than 0 when {action}.")

    @api.constrains('volume_quantity_1', 'volume_cont_1', 'volume_quantity_2', 'volume_cont_2')
    def _check_volume_total_not_zero(self):
        for record in self:
            if record.volume_total == 0:
                raise ValidationError(
                    _("Total volume (TEU) must be greater than 0. Please set valid container types and quantities.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            booking_price = vals.get('booking_price')
            company_booking_price = vals.get('company_booking_price')
            self._validate_booking_prices(booking_price, company_booking_price, action="creating")
            # Optional direct check if volumes are set in create values
            if (not vals.get('volume_quantity_1') and not vals.get('volume_quantity_2')) or \
                    (not vals.get('volume_cont_1') and not vals.get('volume_cont_2')):
                raise ValidationError(
                    _("Cannot create a booking with 0 TEU. Please define valid containers and quantities."))

        # Create the booking first
        bookings = super().create(vals_list)

        # Create linked quotation for each booking
        for booking in bookings:
            booking._create_linked_quotation()

        return bookings

    def write(self, vals):
        for record in self:
            # Check if etd is changing
            if 'etd' in vals:
                new_etd = fields.Date.from_string(vals['etd']) if vals['etd'] else None
                if new_etd and new_etd < fields.Date.today():
                    record._deactivate_expired_always_quotation()

            booking_price = vals.get('booking_price', record.booking_price)
            company_booking_price = vals.get('company_booking_price', record.company_booking_price)
            record._validate_booking_prices(booking_price, company_booking_price, action="updating")

        result = super().write(vals)

        # # Check if fee_type changed and re-link to appropriate quotation
        # if 'fee_type' in vals:
        #     for record in self:
        #         record._auto_link_to_quotation()

        return result

    def _create_linked_quotation(self):
        """Create a linked pricing quotation for this booking"""
        quotation_vals = {
            'fee_type': self.fee_type,
            'sealine_id': self.voyage_id.sealine_id.id if self.voyage_id and self.voyage_id.sealine_id else False,
            'cont_20_price': 120,  # default values following Cosco table
            'cont_40_price': 270,  # default values following Cosco table
            'always': True,
            'valid_from': fields.Date.today(),
            'valid_to': self.etd,
            'active': True,
        }

        quotation = self.env['pricing.quotation'].create(quotation_vals)
        self.pricing_quotation_id = quotation.id

        return quotation

    def action_create_booking(self):
        """Duplicate Booking - Create a new booking with same values"""
        self.ensure_one()
        return {
            'name': _('Duplicate Booking'),
            'type': 'ir.actions.act_window',
            'res_model': 'pricing.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_voyage_id': self.voyage_id.id if self.voyage_id else False,
                'default_volume_quantity_1': self.volume_quantity_1,
                'default_volume_cont_1': self.volume_cont_1,
                'default_volume_quantity_2': self.volume_quantity_2,
                'default_volume_cont_2': self.volume_cont_2,
                'default_booking_price': self.booking_price,
                'default_company_booking_price': self.company_booking_price,
                'default_booking_status': self.booking_status,
                'default_fee_type': self.fee_type,
                'create_booking_from_booking': True,
                'source_booking_id': self.id,
            }
        }

    def action_create_booking_from_quotation(self):
        """Create booking from linked quotation values"""
        self.ensure_one()
        if not self.pricing_quotation_id:
            raise ValidationError(_("No linked pricing quotation found for this booking."))

        # Get sealine from voyage if available, otherwise use quotation's sealine
        sealine_id = False
        if self.voyage_id and self.voyage_id.sealine_id:
            sealine_id = self.voyage_id.sealine_id.id
        elif self.pricing_quotation_id.sealine_id:
            sealine_id = self.pricing_quotation_id.sealine_id.id

        # Find a voyage with the same sealine for default
        default_voyage_id = False
        if sealine_id:
            voyage = self.env['pricing.voyage'].search([
                ('sealine_id', '=', sealine_id)
            ], limit=1)
            default_voyage_id = voyage.id if voyage else False

        return {
            'name': _('Create Booking from Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'pricing.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_voyage_id': default_voyage_id,
                'default_fee_type': self.pricing_quotation_id.fee_type,
                'default_booking_price': self.booking_price,
                'default_company_booking_price': self.company_booking_price,
                'create_booking_from_quotation': True,
                'quotation_id': self.pricing_quotation_id.id,
            }
        }

    @api.constrains('booking_no')
    def _check_unique_booking_no(self):
        """ Ensure unique booking_no """
        for record in self:
            existing_booking = self.env['pricing.booking'].search([
                ('booking_no', 'ilike', record.booking_no),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_booking:
                raise ValidationError(_("The Booking no '%s' already exists.") % record.booking_no)

    @api.depends('volume_quantity_1', 'volume_cont_1', 'volume_quantity_2', 'volume_cont_2')
    def _compute_volume_total(self):
        for record in self:
            total_teu = 0

            # Calculation for first container
            if record.volume_quantity_1 > 0:
                if record.volume_cont_1 in ['20DC', '20RF', '20OT', '20HC']:
                    total_teu += record.volume_quantity_1 * 1
                elif record.volume_cont_1 in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    total_teu += record.volume_quantity_1 * 2

            # Calculation for second container
            if record.volume_quantity_2 > 0:
                if record.volume_cont_2 in ['20DC', '20RF', '20OT', '20HC']:
                    total_teu += record.volume_quantity_2 * 1
                elif record.volume_cont_2 in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    total_teu += record.volume_quantity_2 * 2

            record.volume_total = total_teu

    # Calculate remaining TEU
    @api.depends('sale_line_ids', 'sale_line_ids.order_id.state', 'sale_line_ids.volume_cont', 'volume_total')
    def _compute_teu_usage(self):
        for record in self:
            # Calculate reserved TEU from sale order lines in 'sale' state
            reserved_teu = 0.0
            for line in record.sale_line_ids:
                if line.order_id.state == 'sale' and line.volume_cont:
                    if line.volume_cont in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                        reserved_teu += line.product_uom_qty * 2  # 40ft = 2 TEU
                    elif line.volume_cont in ['20DC', '20RF', '20OT', '20HC']:
                        reserved_teu += line.product_uom_qty * 1  # 20ft = 1 TEU

            record.reserved_teu = reserved_teu
            record.remaining_teu = record.volume_total - reserved_teu

    # Warning for TEU usage
    @api.depends('volume_total', 'reserved_teu', 'remaining_teu')
    def _compute_teu_warning(self):
        for record in self:
            if record.volume_total > 0:
                message = f"""
                    <div class="alert alert-info" role="alert">
                        <strong>TEU Usage Summary:</strong><br/>
                        • Total TEU of booking: <strong>{record.volume_total}</strong><br/>
                        • Reserved TEU (from confirmed orders): <strong>{record.reserved_teu}</strong><br/>
                        • Remaining TEU: <strong>{record.remaining_teu}</strong>
                    </div>
                    """
                if record.remaining_teu < 0:
                    message = f"""
                        <div class="alert alert-danger" role="alert">
                            <strong>⚠️ Over-booking Warning!</strong><br/>
                            • Total TEU of booking: <strong>{record.volume_total}</strong><br/>
                            • Reserved TEU (from confirmed orders): <strong>{record.reserved_teu}</strong><br/>
                            • Over-booked by: <strong>{abs(record.remaining_teu)} TEU</strong>
                        </div>
                        """
                record.teu_warning_message = message
            else:
                record.teu_warning_message = ""

    def _deactivate_expired_always_quotations(self):
        for booking in self:
            if booking.etd and booking.etd < fields.Date.today():
                booking.pricing_quotation_id.write({'active': False})

    @api.model
    def _cron_deactivate_expired_quotations(self):
        """Cron job to deactivate expired quotations"""
        expired_bookings = self.search([
            ('etd', '<', fields.Date.today()),
            ('pricing_quotation_id.always', '=', True),
            ('pricing_quotation_id.active', '=', True)
        ])
        for booking in expired_bookings:
            booking._deactivate_expired_always_quotation()


