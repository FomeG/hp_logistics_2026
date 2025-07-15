from odoo import models, fields


class FreightPurchaseBooking(models.Model):
    _inherit = 'freight.purchase.booking'

    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='booking_id',
        string='Documents'
    )
