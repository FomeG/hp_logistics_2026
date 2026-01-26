from odoo import models, fields
from odoo.addons.hp_components.models.constants import VoyageMode

class SeaFreightRequestLine(models.Model):
    _name = 'freight.purchase.sea.freight.request.line'
    _description = 'Sea Freight Request Line'

    request_id = fields.Many2one(
        comodel_name='freight.purchase.sea.freight.request',
        string="Request",
        required=True,
        ondelete='cascade',
        index=True,
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        string="Carrier",
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        required=True,
        index=True,
    )
    voyage_mode = fields.Selection(
        VoyageMode.SELECT_OPTIONS,
        string="Voyage Mode",
    )
    price = fields.Float(
        string="Price",
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    container_type_id = fields.Many2one(
        comodel_name='container.type',
        string="Container Type",
        domain=[('is_active', '=', True)],
    )
    surcharge_ids = fields.Many2many(
        comodel_name='hp.surcharge',
        string="Surcharge",
    )
    free_time = fields.Char(
        string="Free Time",
    )
    etd = fields.Char()
    note = fields.Text(
        string="Note",
    )