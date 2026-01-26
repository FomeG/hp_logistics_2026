from odoo import models, fields
from odoo.addons.hp_components.models.constant import SurChargeType

class SurCharge(models.Model):
    _name = 'hp.surcharge'
    _description = 'Surcharge'
    _inherit = ['unique.code.mixin','unique.normalized.name.mixin']

    name = fields.Char(
        required=True
    )
    type = fields.Selection(
        SurChargeType.SELECT_OPTIONS,
        required=True,
        default=SurChargeType.SEA_FREIGHT,
    )