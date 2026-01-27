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


    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.assignee_id:
                record.assignee_id = record._get_default_assignee()
        return records

    def _get_default_assignee(self):
        """
        Get default assignee based on POD location.
        1. Find pricing team that manages the POD
        2. Get first team member
        3. If no member found, fallback to pricing department leader
        """
        self.ensure_one()
        pod = self.to_location_id
        if not pod:
            return False

        # Find pricing teams that manage this POD
        teams = self.env['hr.team'].search([
            ('location_ids', 'in', pod.id),
            ('department_id.department_type_id.code', '=', 'pricing'),
        ])

        # Get first team member
        for team in teams:
            if team.user_ids:
                return team.user_ids[0]

        # Fallback to pricing department leader
        pricing_dept = self.env['hr.department'].search([
            ('department_type_id.code', '=', 'pricing')
        ], limit=1)

        if pricing_dept and pricing_dept.manager_id and pricing_dept.manager_id.user_id:
            return pricing_dept.manager_id.user_id

        return False


    def action_assign_pricing_member(self):
        """Open wizard to assign price request to a pricing member"""
        self.ensure_one()
        return {
            'name': _('Assign Price Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'assign.price.request.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_sale.view_assign_price_request_wizard_form').id,
            'target': 'new',
            'context': {
                'default_price_request_id': self.id,
            },
        }

    def action_open_response_form(self):
        """Open popup form to respond to price request"""
        self.ensure_one()
        return {
            'name': _('Response to Price Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.sea.freight.request.line',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_sale.view_sea_freight_request_line_response_form').id,
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_container_type_id': self.container_type_id.id if self.container_type_id else False,
                'default_shipping_line_id': self.shipping_line_id.id if self.shipping_line_id else False,
                'default_voyage_mode': self.voyage_mode,
            },
        }
