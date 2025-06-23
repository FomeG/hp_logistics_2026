from pkg_resources import require

from odoo import models, fields, api
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime


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
    route_id = fields.Many2one(related='quotation_id.route_id', store=True)
    shipping_line_id = fields.Many2one(related='quotation_id.shipping_line_id', store=True)
    teu_volume = fields.Float()
    note = fields.Text()
    line_ids = fields.One2many('freight.purchase.booking.line', 'booking_id', string='Booking Lines')
    booking_mode = fields.Selection([
        ('with_quotation', 'With Quotation'),
        ('without_quotation', 'Without Quotation'),
    ], string='Booking Mode', required=True, default='with_quotation')

    # Temporary fields for quotation creation
    quotation_route_id = fields.Many2one('freight.purchase.route',string='Route',store=False)
    quotation_shipping_line_id = fields.Many2one('res.partner',string="Shipping line", domain="[('is_shipping_line', '=', True)]", store=False)

    total_booking_lines = fields.Char(string="Total Booking Lines", compute='_compute_total_booking_lines', store=False)

    @api.constrains('code')
    def _check_code_required_and_unique(self):
        for record in self:
            if not record.code:
                raise ValidationError("Code is required.")
            existing = self.search([
                ('code', '=', record.code),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(f"Booking code '{record.code}' already exists.")

    @api.onchange('booking_mode')
    def _onchange_booking_mode(self):
        for record in self:
            if record.booking_mode == 'without_quotation':
                record.quotation_id = False

    @api.model_create_multi
    def create(self, vals_list: list[ValuesType]) -> Self:
        for vals in vals_list:
            if vals.get('booking_mode') == 'without_quotation':
                quotation = self.env['freight.purchase.quotation'].create_from_booking_form(vals)
                vals['quotation_id'] = quotation.id

            # Compute vals['name'] manually if quotation is not set => shipping_line, route not exist
            if not vals.get('name'):
                shipping_name = ''
                route_name = ''
                etd_str = ''

                if vals.get('quotation_id'):
                    quotation = self.env['freight.purchase.quotation'].browse(vals['quotation_id'])
                    shipping_name = quotation.shipping_line_id.name or ''
                    route_name = quotation.route_id.name or ''
                elif vals.get('quotation_shipping_line_id') and vals.get('quotation_route_id'):
                    shipping_name = self.env['res.partner'].browse(vals['quotation_shipping_line_id']).name or ''
                    route_name = self.env['freight.purchase.route'].browse(vals['quotation_route_id']).name or ''

                if vals.get('etd'):
                    etd_str = fields.Date.to_date(vals['etd']).strftime('%d-%m-%Y')

                vals['name'] = f"Booking - {shipping_name} - {route_name} - {etd_str}"
        return super().create(vals_list)

    def write(self, vals):
        if 'booking_mode' in vals:
            for record in self:
                if record.id:
                    #prevent to change booking mode
                    if record.booking_mode != vals['booking_mode']:
                        raise UserError(f"You cannot change the booking mode after creation.")
        return super().write(vals)

    # For making the name updated visibly
    @api.depends('shipping_line_id.name', 'route_id.name', 'etd')
    def _compute_name(self):
        for record in self:
            shipping_name = record.shipping_line_id.name or ''
            route_name = record.route_id.name or ''
            formatted_date = ''

            if record.etd and isinstance(record.etd, (date, datetime)):
                formatted_date = record.etd.strftime('%d-%m-%Y')

            record.name = f"Booking - {shipping_name} - {route_name} - {formatted_date}"

    @api.depends('line_ids')
    def _compute_total_booking_lines(self):
        for record in self:
            record.total_booking_lines = "0 Booking Line(s)"
            if record.line_ids:
                record.total_booking_lines = f"{len(record.line_ids)} Booking Line(s)"