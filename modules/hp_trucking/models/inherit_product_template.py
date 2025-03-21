from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    roadline_id = fields.Many2one(
        'trucking.roadline', string="Roadline",
        tracking=True
    )