from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import FeeLineCreateValidator, FeeLineUpdateValidator


class FreightChargeFeeLine(models.Model):
    _name = 'freight.purchase.fee.line'
    _description = 'Fee Line (Charge Detail)'

    name = fields.Char(
        string="Name",
        readonly=True,
        compute='_compute_name',
        store=True,
    )
    fee_id = fields.Many2one(
        'freight.purchase.fee',
        string='Fee/Tariff',
        ondelete='cascade',
        required=True,
        index=True,
    )
    fee_type_id = fields.Many2one(
        'freight.purchase.fee.type',
        string='Fee Type',
        required=True,
        index=True,
        ondelete='restrict',
    )
    container_type_id = fields.Many2one(
        'container.type',
        string='Container Type',
        ondelete='restrict',
    )
    amount = fields.Float(
        string='Amount',
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    charge_at = fields.Selection([
        ('pol', 'POL (Origin)'),
        ('pod', 'POD (Destination)'),
        ('both', 'Both'),
    ],
        string='Charge At',
        default='pol',
        required=True,
        help="Where the fee is charged: POL (Port of Loading), POD (Port of Discharge), or Both"
    )
    # port_id = fields.Many2one(
    #     'location.base',
    #     string="Port",
    # )

    # Related fields for convenience (read-only, for filtering/display)
    shipping_line_id = fields.Many2one(
        'res.partner',
        related='fee_id.shipping_line_id',
        store=True,
        readonly=True,
    )
    date_from = fields.Date(
        related='fee_id.date_from',
        store=True,
        readonly=True,
    )
    date_to = fields.Date(
        related='fee_id.date_to',
        store=True,
        readonly=True,
    )

    # Computed field for UI logic - hide container when fee_type doesn't apply to container
    hide_container = fields.Boolean(
        compute='_compute_hide_container',
        store=False,
    )

    _sql_constraints = [
        ('unique_fee_line',
         'unique(fee_id, fee_type_id, container_type_id, charge_at)',
         'Fee line already exists for this fee type, container type and charge location combination.')
    ]

    @api.depends('fee_type_id')
    def _compute_hide_container(self):
        for record in self:
            # Hide container field if fee_type doesn't apply to container
            record.hide_container = record.fee_type_id.apply_on != 'container' if record.fee_type_id else False

    @api.depends('fee_id', 'fee_type_id', 'container_type_id', 'amount', 'currency_id', 'charge_at')
    def _compute_name(self):
        charge_at_map = {'pol': 'POL', 'pod': 'POD', 'both': 'Both'}
        for record in self:
            parts = []
            if record.fee_type_id:
                parts.append(record.fee_type_id.name)
            if record.charge_at:
                parts.append(f"@{charge_at_map.get(record.charge_at, '')}")
            if record.container_type_id:
                parts.append(record.container_type_id.name)
            if record.amount and record.currency_id:
                parts.append(f"{record.amount:,.0f} {record.currency_id.name}")
            record.name = ' - '.join(parts) if parts else 'New Fee Line'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Set default amount from fee_type_id.amount if not provided
            if vals.get('fee_type_id') and not vals.get('amount'):
                fee_type = self.env['freight.purchase.fee.type'].browse(vals['fee_type_id'])
                if fee_type.amount:
                    vals['amount'] = fee_type.amount

            # Clear container_type_id if fee_type doesn't apply to container
            if vals.get('fee_type_id'):
                fee_type = self.env['freight.purchase.fee.type'].browse(vals['fee_type_id'])
                if fee_type.apply_on != 'container':
                    vals['container_type_id'] = False

        return super().create(vals_list)

    def write(self, vals):
        # If fee_type changes and doesn't apply to container, clear container_type_id
        if vals.get('fee_type_id'):
            fee_type = self.env['freight.purchase.fee.type'].browse(vals['fee_type_id'])
            if fee_type.apply_on != 'container':
                vals['container_type_id'] = False

        return super().write(vals)

    @api.onchange('fee_type_id')
    def _onchange_fee_type_id(self):
        if self.fee_type_id:
            # Set default amount from fee_type
            if self.fee_type_id.amount and not self.amount:
                self.amount = self.fee_type_id.amount
            
            # Clear container if fee_type doesn't apply to container
            if self.fee_type_id.apply_on != 'container':
                self.container_type_id = False