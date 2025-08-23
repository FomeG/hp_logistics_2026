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
        default='n/a',
    )
    apply_on = fields.Selection([
        ('container', 'Container'),
        ('port', 'Port'),
        ('n/a', 'N/A'),
    ], required=True, string="Apply on",default='n/a')
    amount = fields.Float()
    active = fields.Boolean(
        default=True,
        required=True
    )

    @api.constrains('apply_on', 'direction')
    def _check_apply_on_direction_consistency(self):
        for record in self:
            if record.apply_on == 'container' and record.direction == 'n/a':
                raise ValidationError("Container fee types cannot have direction 'N/A'.")

    @api.model_create_multi
    def create(self, vals_list):
        validated_list = []
        for vals in vals_list:
            validated, errors = FeeValidator.validate_fee_type(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            vals['name'] = f"{vals['name']} ({validated.get('direction') or vals.get('direction') or ''})"
            validated_list.append(vals)
        return super().create(validated_list)

    def write(self, vals):
        current_record = self if isinstance(self, type(self)) else self[0]
        validated, errors = FeeValidator.validate_fee_type(vals, self.env, 'write', record=current_record)
        if errors:
            raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)