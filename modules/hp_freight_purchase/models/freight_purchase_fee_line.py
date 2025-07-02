from odoo import models, fields


class FreightChargeFeeLine(models.Model):
    _name = 'freight.purchase.fee.line'
    _description = 'Container Type Charges'

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
    _sql_constraints = [
        ('unique_container_fee', 'unique(fee_id, container_type_id)', 'Fee already exists for this container.')
    ]
