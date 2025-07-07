from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import FeeLineCreateValidator, FeeLineUpdateValidator


class FreightChargeFeeLine(models.Model):
    _name = 'freight.purchase.fee.line'
    _description = 'Container Type Charges'

    name = fields.Char(
        string="Name",
        readonly=True,
        compute='_compute_name',
        store=True,
    )
    fee_id = fields.Many2one(
        'freight.purchase.fee',
        ondelete='cascade',
        required=True
    )
    container_type_id = fields.Many2one(
        'container.type',
        required=True
    )
    amount = fields.Float(
        required=True
    )

    # New Related Fields
    shipping_line_id = fields.Many2one(
        'res.partner',
        related='fee_id.shipping_line_id',
        store=True,
        readonly=True
    )

    fee_type_id = fields.Many2one(
        'freight.purchase.fee.type',
        related='fee_id.fee_type_id',
        store=True,
        readonly=True
    )

    date_from = fields.Date(
        related='fee_id.date_from',
        store=True,
        readonly=True
    )

    date_to = fields.Date(
        related='fee_id.date_to',
        store=True,
        readonly=True
    )

    _sql_constraints = [
        ('unique_container_fee', 'unique(fee_id, container_type_id)', 'Fee already exists for this container.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        validated_list = []
        for vals in vals_list:
            validated, errors = FeeLineCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            validated_list.append(validated)
        return super().create(validated_list)

    def write(self, vals):
        for record in self:
            validated, errors = FeeLineUpdateValidator.validate(vals, self.env, record.id)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(validated if validated else vals)

    @api.depends('fee_id','container_type_id')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.fee_id.name or ''} - {record.container_type_id.name or ''}"

