from odoo import models, fields
from odoo.addons.hp_components.models.constant import PriorityLevel
from odoo.addons.hp_components.models.constant import PriceRequestState
from odoo.addons.hp_components.models.constant import VoyageMode
from odoo.addons.hp_components.models.constant import ServiceType

class SeaFreightRequest(models.Model):
    _name = 'freight.purchase.sea.freight.request'
    _description = 'Sea Freight Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name =  fields.Char(
        string='Name',
        required=True,
        compute='_compute_name',
        store=False
    )
    service_type = fields.Selection(
        ServiceType.SELECT_OPTIONS,
        string="Service Type",
        default=ServiceType.EXPORT,
        required=True,
    )
    commodity = fields.Char(
        string="Commodity",
        tracking=True
    )
    commodity_hs_code = fields.Char(
        string="Commodity HS Code",
    )
    from_location_id = fields.Many2one(
        string='POL',
        comodel_name='location.base',
        required=True,
        tracking=True,
        domain="[('type', '=', 'port')]",
        index=True,
    )
    to_location_id = fields.Many2one(
        string='POD',
        comodel_name='location.base',
        required=True,
        tracking=True,
        index=True,
    )
    free_time = fields.Char(
        string="Free Time",
    )
    voyage_mode = fields.Selection(
        VoyageMode.SELECT_OPTIONS,
        string="Voyage Mode",
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        string="Shipping Line preferred",
        index=True,
    )
    quantity = fields.Integer(
        string="Quantity",
        tracking=True
    )
    container_type_id = fields.Many2one(
        comodel_name='container.type',
        string="Container Type preferred",
        domain=[('is_active', '=', True)],
    )
    weight = fields.Float(
        string="Weight",
        tracking=True,
        help="To detect if the cargo is heavy or not"
    )
    etd = fields.Date(
        string="ETD",
        tracking=True,
        default=fields.Date.today()
    )
    client = fields.Many2one(
        comodel_name='res.partner.client',
        string="Client",
        tracking=True
    )
    note = fields.Text(
        string="Note"
    )
    state = fields.Selection(
        PriceRequestState.SELECT_OPTIONS,
        string="Status",
        compute='_compute_state',
    ),
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Sale Order",
        tracking=True
    )
    request_line_ids = fields.One2many(
        comodel_name='freight.purchase.sea.freight.request.line',
        inverse_name='request_id',
        string="Rates",
    )
    def _compute_name(self):
        for record in self:
            record.name = f"Sea Freight Request: {record.from_location_id.name} to {record.to_location_id.name}"

    def _compute_state(self):
        for record in self:
            if record.request_line_ids.length > 0:
                record.state = PriceRequestState.DONE