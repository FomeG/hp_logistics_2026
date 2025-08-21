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
        # required=True
    )
    container_type_id = fields.Many2one(
        'container.type',
        # required=True,
        ondelete='cascade'
    )
    amount = fields.Float(
        # required=True
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
    port_id = fields.Many2one("freight.purchase.port", string="Port")

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
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        # related='port_id.country_id',
        store=True,
    )

    # _sql_constraints = [
    #     ('unique_container_fee', 'unique(fee_id, container_type_id)', 'Fee already exists for this container.')
    # ]

    @api.model_create_multi
    def create(self, vals_list):
        new_lines = []
        for vals in vals_list:
            fee = self.env['freight.purchase.fee'].browse(vals.get('fee_id'))
            # Set default amount from fee_type_id.amount if not provided
            if fee.fee_type_id and not vals.get('amount'):
                vals['amount'] = fee.fee_type_id.amount
            # Validate port_id against country_id
            if vals.get('port_id') and vals.get('country_id'):
                port = self.env['freight.purchase.port'].browse(vals['port_id'])
                if port.country_id.id != vals['country_id']:
                    raise ValidationError(
                        f"Port {port.name} does not belong to country {self.env['res.country'].browse(vals['country_id']).name}.")
            # If user selects country and no port
            if fee.country_id and not vals.get('port_id'):
                ports = self.env['freight.purchase.port'].search([('country_id', '=', fee.country_id.id)])
                for port in ports:
                    line_vals = vals.copy()
                    line_vals['port_id'] = port.id
                    line_vals['country_id'] = fee.country_id.id
                    line_vals['amount'] = fee.fee_type_id.amount if fee.fee_type_id else 0.0
                    if fee.fee_type_id.apply_on != 'container':
                        line_vals['container_type_id'] = False
                    new_lines.append(line_vals)
            else:
                new_lines.append(vals)
        return super().create(new_lines)

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

    @api.onchange('fee_id')
    def _onchange_fee_id(self):
        if self.fee_id and self.fee_id.fee_type_id:
            self.amount = self.fee_id.fee_type_id.amount  # Set amount from fee_type_id
            if self.fee_id.country_id:
                self.country_id = self.fee_id.country_id
                return {
                    'domain': {
                        'port_id': [('country_id', '=', self.fee_id.country_id.id)]
                    }
                }
        return {'domain': {'port_id': []}}

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            return {
                'domain': {
                    'port_id': [('country_id', '=', self.country_id.id)]
                }
            }
        return {'domain': {'port_id': []}}

    @api.onchange('fee_type_id')
    def _onchange_fee_type_id(self):
        if self.fee_type_id:
            self.amount = self.fee_type_id.amount