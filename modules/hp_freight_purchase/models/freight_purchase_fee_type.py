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

    # Parent field for hierarchy
    parent_id = fields.Many2one(
        'freight.purchase.fee.type',
        string='Parent Fee Type',
        ondelete='cascade',
        domain="[('parent_id', '=', False)]",
        index=True
    )

    # Child relationships
    child_ids = fields.One2many(
        'freight.purchase.fee.type',
        'parent_id',
        string='Child Fee Types'
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

    description = fields.Char(
        string="Description",
        help="Short description for the fee type"
    )

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for fee_type in self:
            if fee_type.parent_id:
                fee_type.complete_name = '%s / %s' % (fee_type.parent_id.complete_name, fee_type.name)
            else:
                fee_type.complete_name = fee_type.name

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for fee_type in self:
            if fee_type.parent_id and fee_type.parent_id == fee_type:
                raise ValidationError("A fee type cannot be its own parent.")
            # Check for circular references
            if fee_type.parent_id:
                current = fee_type.parent_id
                while current:
                    if current == fee_type:
                        raise ValidationError("Circular reference detected in fee type hierarchy.")
                    current = current.parent_id
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