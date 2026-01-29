from odoo import models, fields, api, _
from odoo.addons.hp_components.models.constants import PriceRequestState
from odoo.addons.hp_components.models.constants import VoyageMode
from odoo.addons.hp_components.models.constants import ServiceType
from odoo.addons.hp_components.models.constants import DepartmentTypeCode
from ...hp_components.services.activity_service import ActivityService
from ...hp_components.services.department_service import DepartmentService
import json
from datetime import datetime, date

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
    parent_id = fields.Many2one(
        comodel_name='freight.purchase.sea.freight.request',
        string="Parent Request",
        help="Original price request this was duplicated from"
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
        compute="_compute_assignee_id",
    )
    number_of_response = fields.Integer(
        string="Number of Responses",
        compute="_compute_number_of_response",
        store=False
    )
    active = fields.Boolean(string="Active", default=True)

    allow_from_location_ids = fields.Many2many('location.base', compute='_compute_allow_from_location_ids', store=False)
    allow_to_location_ids = fields.Many2many('location.base', compute='_compute_allow_to_location_ids', store=False)

    @api.depends('from_location_id', 'to_location_id')
    def _compute_assignee_id(self):
        Department = DepartmentService(self.env)
        for record in self:
            creator_branch_id = record.create_uid.employee_id.department_id.branch_id.id
            sale_manager=  Department.get_department_manager_by_type_and_branch(DepartmentTypeCode.SALE, creator_branch_id)
            record.assignee_id = sale_manager

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

    @api.depends('service_type')
    def _compute_allow_from_location_ids(self):
        for rec in self:
            is_local = True if rec.service_type == ServiceType.EXPORT else False
            rec.allow_from_location_ids = self.env['location.base'].search([('is_local', '=', is_local)])

    @api.depends('service_type',)
    def _compute_allow_to_location_ids(self):
        for rec in self:
            is_local = False if rec.service_type == ServiceType.EXPORT else True
            rec.allow_to_location_ids = self.env['location.base'].search([('is_local', '=', is_local)])


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

    def _handle_notify_on_create(self):
        Department = DepartmentService(self.env)
        creator_branch_id = self.create_uid.employee_id.department_id.branch_id.id if self.create_uid.employee_id.department_id.branch_id else False
        
        if not creator_branch_id:
            return True
            
        sale_manager = Department.get_department_manager_by_type_and_branch(DepartmentTypeCode.SALE, creator_branch_id)

        if not sale_manager:
            return True

        service = ActivityService(
            env=self.env,
            model_name='freight.purchase.sea.freight.request',
            record_id=self.id,
            user_ids=sale_manager.id
        )

        service._create_activity_by_type(
            summary=f"New price request has been created by {self.create_uid.name}",
            note=''
        )

        return True
    
    def _cron_inactive_by_etd(self):
        today = fields.Date.today()
        requests = self.sudo().search([
            ('active', '=', True),
            ('state', '=',  PriceRequestState.DONE),
        ])
        for request in requests:
            if request.etd and request.etd < today:
                request.active = False
            else:
                expired_lines = request.request_line_ids.filtered(
                    lambda l: l.etd and any(
                        datetime.strptime(etd_str, "%Y-%m-%d").date() < today
                        for etd_str in json.loads(l.etd)
                    )
                )
                if expired_lines:
                    request.active = False
        return 

    def copy(self, default=None):
        """Override copy to set parent_id and reset etd to today"""
        default = dict(default or {})
        default.update({
            'parent_id': self.id,
            'etd': fields.Date.today(),
        })
        return super().copy(default)
