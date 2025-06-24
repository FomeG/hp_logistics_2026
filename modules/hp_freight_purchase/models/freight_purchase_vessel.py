from odoo import models, fields, api

class FreightPurchaseVessel(models.Model):
    _name = 'freight.purchase.vessel'
    _description = 'Vessel'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin','unique.normalized.name.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)
    booking_ids = fields.One2many('freight.purchase.booking', 'vessel_id', string='Bookings')

    total_bookings = fields.Char(string="Total Bookings", compute='_compute_total_booking', store=False)

    @api.depends('booking_ids')
    def _compute_total_booking(self):
        for vessel in self:
            if vessel.booking_ids:
                total = len(vessel.booking_ids)
                vessel.total_bookings = f"{total} Booking(s)"
            else:
                vessel.total_bookings = "0 Booking(s)"


