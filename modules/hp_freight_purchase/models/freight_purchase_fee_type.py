from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import  FeeValidator

class FreightPurchaseFeeType(models.Model):
    _name = 'freight.purchase.fee.type'
    _description = 'Freight Purchase Fee Type'
    _inherit = ['unique.code.mixin','unique.normalized.name.mixin']
    name = fields.Char(
        string='Name',
        required=True
    )
    type = fields.Selection(
        string='Type',
        selection=[
            ('l', 'L'),
            ('d', 'D'),
            ('l/d', 'L/D'),
        ],
        default='l',
    )
    is_active = fields.Boolean(default=True, required=True)

    @api.model_create_multi
    def create(self, vals_list):
        validated_list = []
        for vals in vals_list:
            validated, errors = FeeValidator.validate_fee_type(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            validated['name'] = f"{validated['name']} ({validated['type']})"
            validated_list.append(validated)

        return super().create(validated_list)