from odoo import models, fields, _
from odoo.exceptions import UserError
from ...hp_components.models import constants

class ProductCategory(models.Model):
    _inherit = "product.category"

    service_type = fields.Selection(
        constants.ServiceType.SELECT_OPTIONS,
        string="Service Type",
        default=constants.ServiceType.EXPORT,
        required=True,
    )
