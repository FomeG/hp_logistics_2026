from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    _order = 'create_date desc'


    is_shipping_line = fields.Boolean(string='Is a Shipping Line', default=False)

    booking_ids = fields.One2many('freight.purchase.booking', 'shipping_line_id', string='Bookings')
    quotation_ids = fields.One2many('freight.purchase.quotation', 'shipping_line_id', string='Quotations')

    total_bookings = fields.Char(string="Total Bookings", compute='_compute_total_booking', store=False)
    total_quotations = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_shipping_line = vals.get('is_shipping_line', False)
            email = vals.get('email')
            if is_shipping_line and not email:
                raise ValidationError("Shipping line email is required.")
        return super().create(vals_list)
    
    def write(self, vals):
        for record in self:
            is_shipping_line = vals.get('is_shipping_line', record.is_shipping_line)
            email = vals.get('email', record.email)
            if is_shipping_line and not email:
                raise ValidationError("Shipping line email is required.")

        return super().write(vals)

    @api.depends('booking_ids')
    def _compute_total_booking(self):
        for record in self:
            if record.booking_ids:
                total = len(record.booking_ids)
                record.total_bookings = f"{total} Booking(s)"
            else:
                record.total_bookings = "0 Booking(s)"

    @api.depends('quotation_ids')
    def _compute_total_quotation(self):
        for record in self:
            if record.quotation_ids:
                total = len(record.quotation_ids)
                record.total_quotations = f"{total} Quotation(s)"
            else:
                record.total_quotations = "0 Quotation(s)"

    #todo require name + email