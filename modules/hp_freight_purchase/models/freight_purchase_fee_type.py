from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import FeeValidator

class FreightPurchaseFeeType(models.Model):
    _name = 'freight.purchase.fee.type'
    _description = 'Freight Purchase Fee Type'
    _inherit = ['unique.code.mixin','unique.normalized.name.mixin']
    name = fields.Char(
        string='Name',
        required=True
    )
    direction = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('n/a', 'N/A'),
    ],
        required=True,
        default='import',
    )
    is_common = fields.Boolean(
        default=False
    )
    amount = fields.Float(
        required=False
    )
    active = fields.Boolean(
        default=True,
        required=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        validated_list = []
        for vals in vals_list:
            validated, errors = FeeValidator.validate_fee_type(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            vals['name'] = f"{vals['name']} ({vals['direction'] or validated['direction'] or ''})"
            validated_list.append(vals)
        return super().create(validated_list)

    def write(self, vals):
        current_record = self if isinstance(self, type(self)) else self[0]
        new_direction = vals.get('direction', current_record.direction)
        new_is_common = vals.get('is_common', current_record.is_common)
        if new_direction == 'n/a' and not new_is_common:
            raise ValidationError("Cannot select direction is 'n/a' when Is Common is uncheck.")
        validated, errors = FeeValidator.validate_fee_type(vals, self.env,'write',record=current_record)
        if errors:
            raise ValidationError("\n".join([f"• {e}" for e in errors]))
        if 'is_common' in validated.keys() and validated['is_common']:
            vals['direction'] = 'n/a'
        return super().write(vals)

    @api.onchange('is_common')
    def _onchange_is_common(self):
        if not self.is_common:
            self.amount = 0.0
            self.direction = 'import'
        else:
            self.direction = 'n/a'