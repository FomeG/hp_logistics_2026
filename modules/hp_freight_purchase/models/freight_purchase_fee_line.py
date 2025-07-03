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
