from odoo import models, fields, api, _
from odoo.addons.hp_components.models.constants import PriceRequestState
from odoo.addons.hp_components.models.constants import VoyageMode
from odoo.addons.hp_components.models.constants import ServiceType

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
        store=True
    )

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

    assignee_id = fields.Many2one(
        'res.users',
        string='Assignee',
        store=True,
    )
    number_of_response = fields.Integer(
        string="Number of Responses",
        compute="_compute_number_of_response",
        store=False
    )

    @api.depends('request_line_ids')
    def _compute_number_of_response(self):
        for record in self:
            record.number_of_response = len(record.request_line_ids)

    @api.depends('from_location_id', 'to_location_id')    
    def _compute_name(self):
        for record in self:
            if record.from_location_id and record.to_location_id:
                record.name = f"Sea Freight Request: {record.from_location_id.name} to {record.to_location_id.name}"
            else:
                record.name = False

    @api.depends('request_line_ids')
    def _compute_state(self):
        for record in self:
            if len(record.request_line_ids) > 0:
                record.state = PriceRequestState.DONE
            else:
                record.state = PriceRequestState.OPEN