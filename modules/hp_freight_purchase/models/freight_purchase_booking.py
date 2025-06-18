from pkg_resources import require

from odoo import models, fields, api
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError, UserError


class FreightPurchaseBooking(models.Model):

    _name = 'freight.purchase.booking'
    _description = 'Freight Purchase Booking'
    _inherit = ['mail.thread','unique.code.mixin', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, string='Booking Name')
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
    ], string='Booking Mode', required=True, default='with_quotation', store=False)

    # Temporary fields for quotation creation
    quotation_route_id = fields.Many2one('freight.purchase.route',string='Route',store=False)
    quotation_shipping_line_id = fields.Many2one('res.partner',string="Shipping line", domain="[('is_shipping_line', '=', True)]", store=False)

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
        return super().create(vals_list)

    def write(self, vals):
        if 'booking_mode' in vals:
            for record in self:
                if record.id:
                    #prevent to change booking mode
                    if record.booking_mode != vals['booking_mode']:
                        raise UserError(f"You cannot change the booking mode after creation.")
        return super().write(vals)