from datetime import date, datetime
from itertools import count

from odoo import models, fields, api
from odoo.addons.base.models.ir_actions_report import available


class FreightPurchaseQuotation(models.Model):
    _name = 'freight.purchase.quotation'
    _description = 'Freight Purchase Quotation'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, string='Quotation Name', compute='_compute_name', store=True, tracking=True)
    route_id = fields.Many2one('freight.purchase.route', required=True, tracking=True)
    shipping_line_id = fields.Many2one('res.partner', domain="[('is_shipping_line', '=', True)]", required=True, tracking=True)

    available_from = fields.Date(required=True, tracking=True)
    available_to = fields.Date(required=True, tracking=True)
    fees = fields.Many2many('freight.purchase.fee', string='Fees', tracking=True)
    note = fields.Text()
    is_active = fields.Boolean(default=True, tracking=True)
    line_ids = fields.One2many('freight.purchase.quotation.line', 'quotation_id', tracking=True)
    total_quotation_lines = fields.Char(string="Total Quotation Lines", compute='_compute_total_quotation_lines', store=False)
    str_fees = fields.Char(
        string="Fees",
        compute='_compute_fees',
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

    @api.depends('fees')
    def _compute_fees(self):
        for quotation in self:
            if not quotation.fees:
                quotation.str_fees = f"No fees applied"
            else:
                names = []
                for fee in quotation.fees:
                    names.append(fee.name)
                quotation.str_fees = ", ".join(names)

    # For making the name updated visibly
    @api.depends('shipping_line_id.name', 'route_id.name', 'available_to')
    def _compute_name(self):
        for record in self:
            shipping_name = record.shipping_line_id.name or ''
            route_name = record.route_id.name or ''

            # Check that available_to is a valid date
            if record.available_to and isinstance(record.available_to, (date, datetime)):
                formatted_date = record.available_to.strftime('%d-%m-%Y')
            else:
                formatted_date = ''
            if shipping_name != '' and route_name != '':
                record.name = f"Quotation - {shipping_name} - {route_name} - {formatted_date}"

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