from datetime import date, datetime
from itertools import count
from odoo import models, fields, api
from odoo.addons.base.models.ir_actions_report import available
from odoo.exceptions import ValidationError
from ..validators.quotation_validator import QuotationCreateValidator, QuotationUpdateValidator


class FreightPurchaseQuotation(models.Model):
    _name = 'freight.purchase.quotation'
    _description = 'Freight Purchase Quotation'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Quotation Name',
        required=True,
        compute='_compute_name',
        store=True,
        tracking=True)
    route_id = fields.Many2one(
        'freight.purchase.route',
        required=True,
        tracking=True
    )
    pol_id = fields.Many2one(
        related='route_id.pol_id',
        string='POL',
        store=True,
        index=True,
    )
    pod_id = fields.Many2one(
        related='route_id.pod_id',
        string='POD',
        store=True,
        index=True,
    )
    direction = fields.Selection(
        related='route_id.direction',
        store=True
    )
    shipping_line_id = fields.Many2one(
        'res.partner',
        domain="[('is_shipping_line', '=', True)]",
        required=True,
        tracking=True
    )

    available_from = fields.Date(
        required=True,
        tracking=True
    )
    available_to = fields.Date(
        required=True,
        tracking=True
    )
    note = fields.Text()
    is_active = fields.Boolean(
        default=True,
        tracking=True
    )
    line_ids = fields.One2many(
        'freight.purchase.quotation.line',
        'quotation_id',
        tracking=True
    )
    fee_ids = fields.One2many(
        comodel_name="freight.purchase.quotation.fee",
        inverse_name="quotation_id",
        string="Common Fees"
    )
    total_quotation_lines = fields.Char(
        string="Total Quotation Lines",
        compute='_compute_total_quotation_lines',
        store=False
    )
    str_available = fields.Char(
        string="Available",
        compute='_compute_str_available',
        store=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = QuotationCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            # Compute vals['name']
            if not vals.get('name'):
                shipping_line_id = vals.get('shipping_line_id')
                route_id = vals.get('route_id')
                available_to = vals.get('available_to')

                if shipping_line_id and route_id and available_to:
                    shipping_name = self.env['res.partner'].browse(shipping_line_id).name or ''
                    route_name = self.env['freight.purchase.route'].browse(route_id).name or ''
                    formatted_date = ''
                    if available_to:
                        formatted_date = fields.Date.to_date(available_to).strftime('%d-%m-%Y')

                    vals['name'] = f"Quotation - {shipping_name} - {route_name} - {formatted_date}"
                else:
                    vals['name'] = 'Quotation'

        # Compute code
        records = super().create(vals_list)

        for record in records:
            if not record.code or record.code == '/':
                record.code = super(FreightPurchaseQuotation, record)._generate_code_from_name(record.name or '')

        return records
    
    def write(self, vals):
        for record in self:
            validated, errors = QuotationUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)

    # For making the name updated visibly
    @api.depends('shipping_line_id.name', 'route_id.name', 'available_to')
    def _compute_name(self):
        for record in self:
            if record.shipping_line_id and record.route_id and record.available_to:
                shipping_name = record.shipping_line_id.name or ''
                route_name = record.route_id.name or ''
                formatted_date = ''
                if isinstance(record.available_to, (date, datetime)):
                    formatted_date = record.available_to.strftime('%d-%m-%Y')

                record.name = f"Quotation - {shipping_name} - {route_name} - {formatted_date}"
            else:
                # Keep the name empty until all fields are filled
                record.name = False

    @api.model
    def create_from_booking_form(self, booking_form):
        return self.create({
            'route_id': booking_form.get('quotation_route_id'),
            'shipping_line_id': booking_form.get('quotation_shipping_line_id'),
            'available_from': fields.Date.today(),
            'available_to': booking_form.get('etd'),
        })
    @api.depends('line_ids')
    def _compute_total_quotation_lines(self):
        for record in self:
            record.total_quotation_lines = "0 Quotation Line(s)"
            if record.line_ids:
                record.total_quotation_lines = f"{len(record.line_ids)} Quotation Line(s)"
    def _compute_str_available(self):
        for record in self:
            record.str_available = ''
            if record.available_from and record.available_to:
                record.str_available = f"{record.available_from.strftime('%d-%m-%Y')} - {record.available_to.strftime('%d-%m-%Y')}"
    #todo require name + email