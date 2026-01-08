from odoo import models, fields, api
from odoo.addons.hp_components.models.constants import TransportMode


class GetFreightPriceWizard(models.TransientModel):
    _name = 'hp_sale.freight.price.wizard.line'
    _description = 'Freight Price Wizard Line'

    wizard_id = fields.Many2one(
        comodel_name='hp_sale.freight.price.wizard'
    )
    source_ref = fields.Reference(
        selection=[
            ('product.template.selling.week.line', 'Sea Freight'),
            ('route.base', 'Truck Freight'),
        ],
        string="Source Price",
    )
    selected = fields.Boolean(
        string="Select",
        default=False
    )
    name = fields.Char(
        compute='_compute_name',
    )
    transport_mode = fields.Selection(
        TransportMode.SELECT_OPTIONS,
        string="Transport Mode"
    )
    from_location_id = fields.Many2one(
        comodel_name='location.base',
        string="From Location",
    )
    to_location_id = fields.Many2one(
        comodel_name='location.base',
        string="To Location",
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        string="Shipping Line",
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
    )
    container_type_id = fields.Many2one(
        comodel_name='container.type',
        string="Container",
        domain=[('is_active', '=', True)],
    )
    price = fields.Monetary(
        string="Price",
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    note = fields.Char(
        string="Note",
        compute='_compute_note',
    )
    suggestion = fields.Boolean(
        default=False,
    )
    def _compute_note(self):
        for record in self:
            record.note = ""
            if not record.price:
                record.note = f"There is no freight price available in this period."

    @api.depends('transport_mode')
    def _compute_name(self):
        for record in self:
            if record.transport_mode == TransportMode.SEA:
                record.name = f"Sea Freight {record.from_location_id.name} - {record.to_location_id.name}"
            else:
                record.name = f"Truck Freight {record.from_location_id.name} - {record.to_location_id.name}"