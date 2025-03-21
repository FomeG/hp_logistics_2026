from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from datetime import date

class ProductTemplate(models.Model):
    _inherit = "product.template"

    sealine_id = fields.Many2one(
        'pricing.sealine', string="Sealine",
        tracking=True
    )
    booking_id = fields.Many2one(
        'pricing.booking', string="Booking",
        domain="[('voyage_id.etd', '>', '{}')]".format(date.today()),
        tracking=True
    )