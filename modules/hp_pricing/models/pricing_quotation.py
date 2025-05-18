from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

class PricingQuotation(models.Model):
    _name = 'pricing.quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Quotation'
    _rec_name = 'display_name'
    _order = 'write_date desc'

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    cont_20_price = fields.Float('Cont 20 Price', tracking=True)
    cont_40_price = fields.Float('Cont 40 Price', tracking=True)

    fee_type = fields.Selection(selection=[
        ('SBJ', 'SBJ'),
        ('Allin', 'Allin'),
    ], string='Booking Fee Type', default='Allin', tracking=True)

    sealine_id = fields.Many2one(
        'pricing.sealine', string="Sealine",
        tracking=True
    )

    current_volume_total = fields.Integer(string='Total Current Volume (TEU)', compute='_compute_volume_total', store=True)

    valid_from = fields.Date(
        string="Valid From",
    )
    valid_to = fields.Date(
        string="Valid To",
    )

    booking_ids = fields.One2many(
        'pricing.booking',
        'pricing_quotation_id',
        string="Bookings"
    )

    # One2many field to see all sales order lines using this booking
    sale_line_ids = fields.One2many(
        'sale.order.line',
        'pricing_quotation_id',
        string="Sales Order Lines",
        copy=False
    )

    active = fields.Boolean(default=True)

    # display_name
    @api.depends('fee_type', 'valid_from', 'valid_to')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.fee_type} valid from {record.valid_from} to {record.valid_to}"

    @api.constrains('display_name')
    def _check_unique_display_name(self):
        """ Ensure unique display_name """
        for record in self:
            existing_quotation = self.env['pricing.quotation'].search([
                ('display_name', 'ilike', record.display_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_quotation:
                raise ValidationError(_("The Quotation '%s' already exists.") % record.display_name)

    @api.depends('booking_ids.volume_total')
    def _compute_volume_total(self):
        for record in self:
            total_teu = sum(booking.volume_total for booking in record.booking_ids if booking.volume_total)
            record.current_volume_total = total_teu


    def action_add_bookings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Select Bookings'),
            'res_model': 'pricing.booking',
            'view_mode': 'tree',
            'target': 'new',
            'domain': [('pricing_quotation_id', '=', False)],  # only unlinked
            'context': {
                'default_pricing_quotation_id': self.id,
            }
        }

