from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    is_shipping_line = fields.Boolean(string='Is a Shipping Line', default=False)
