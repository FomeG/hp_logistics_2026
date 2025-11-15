from odoo import models, fields


class CsBooking(models.Model):
    _name = "cs.booking"
    _description = "Booking Information"
    _inherit = ['cs.order.detail']

    Booking_code = fields.Char(
        related='booking_id.code',
        string="Booking Code",
        help="Booking Code",
        index=True,
        store=True,
        readonly=True,
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        string="Shipping Line",
        related='booking_id.shipping_line_id',
        store=True,
        index=True,
    )
    voyage = fields.Char(
        string="Voyage",
        related="booking_id.voyage",
        store=False,
    )
    etd = fields.Date(
        string="ETD",
        related="booking_id.etd",
    )
    eta = fields.Date(
        string="ETA",
    )
    vessel_id = fields.Many2one(
        related="booking_id.vessel_id",
        comodel_name='freight.purchase.vessel',
        string="Vessel",
        store=False,
    )
    pol_id = fields.Many2one(
        comodel_name='freight.purchase.port',
        string="Port of Loading",
        related = 'booking_id.pol_id',
        store=False,
    )
    pod_id = fields.Many2one(
        comodel_name='freight.purchase.port',
        string="Port of Discharge",
        related='booking_id.pod_id',
        store=False,
    )