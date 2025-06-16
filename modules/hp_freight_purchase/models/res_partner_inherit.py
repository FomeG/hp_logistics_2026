from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    is_shipping_line = fields.Boolean(string='Is a Shipping Line', default=False)

    booking_ids = fields.One2many('freight.purchase.booking', 'shipping_line_id', string='Bookings')
    quotation_ids = fields.One2many('freight.purchase.quotation', 'shipping_line_id', string='Quotations')

    total_bookings = fields.Char(string="Total Bookings", compute='_compute_total_booking', store=False)
    total_quotations = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)

    @api.depends('booking_ids')
    def _compute_total_booking(self):
        for record in self:
            if record.total_bookings:
                total = len(record.booking_ids)
                record.total_bookings = f"{total} Booking(s)"
            else:
                record.total_bookings = "0 Booking(s)"

    @api.depends('quotation_ids')
    def _compute_total_quotation(self):
        for record in self:
            if record.total_quotations:
                total = len(record.quotation_ids)
                record.total_quotations = f"{total} Quotation(s)"
            else:
                record.total_quotations = "0 Quotation(s)"