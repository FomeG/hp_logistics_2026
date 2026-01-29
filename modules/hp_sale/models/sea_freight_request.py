from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models.constants import PriceRequestState
from odoo.addons.hp_components.models.constants import VoyageMode
from odoo.addons.hp_components.models.constants import ServiceType
from odoo.addons.hp_components.models.constants import DepartmentTypeCode
from ...hp_components.services.activity_service import ActivityService
from ...hp_components.services.department_service import DepartmentService
import json
from datetime import datetime, date, timedelta

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
    sea_freight_id = fields.Many2one(
        comodel_name='product.template.selling.week',
        string="Sea Freight",
        help="Generated sea freight from this price request"
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


    @api.constrains('etd')
    def _check_etd_future_date(self):
        """Validate that ETD must be greater than current date if provided"""
        today = fields.Date.today()
        for record in self:
            if record.etd and record.etd <today:
                raise ValidationError(_("ETD must be greater than current date."))

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

    def action_generate_sea_freight(self):
        """Generate sea freight from done price request"""
        self.ensure_one()
        
        if self.state != PriceRequestState.DONE:
            raise ValidationError(_("Only 'Done' price requests can generate sea freight."))
        
        if not self.request_line_ids:
            raise ValidationError(_("No response lines found to generate sea freight."))
        
        if self.sea_freight_id:
            raise ValidationError(_("Sea freight has already been generated for this price request."))
        
        # 1. Find or create selling week based on ETD
        selling_week = self._get_or_create_selling_week()
        
        # 2. Get sale team by POD and branch
        team = self._get_sale_team()
        
        # 3. Find or create sea freight (ProductTemplateSellingWeek)
        sea_freight = self._get_or_create_sea_freight(selling_week, team)
        
        # 4. Create sea freight lines from response lines
        self._create_sea_freight_lines(sea_freight)
        
        # 5. Set sea freight id into price request
        self.sea_freight_id = sea_freight.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sea Freight Generated'),
                'message': _('Sea freight has been generated successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _get_or_create_selling_week(self):
        """Find or create selling week based on ETD"""
        SellingWeek = self.env['selling.week']
        
        # Use ETD from price request, or today if not set
        etd = self.etd or fields.Date.today()
        
        # Find week where ETD falls between start_date and end_date
        selling_week = SellingWeek.search([
            ('start_date', '<=', etd),
            ('end_date', '>=', etd),
        ], limit=1)
        
        if not selling_week:
            # Calculate week start (Monday) and end (Sunday)
            # ETD's week
            week_start = etd - timedelta(days=etd.weekday())
            week_end = week_start + timedelta(days=6)
            
            # Get ISO week number
            week_number = etd.isocalendar()[1]
            year = etd.year
            
            selling_week = SellingWeek.create({
                'name': f"Tuần {week_number} - {year}",
                'start_date': week_start,
                'end_date': week_end,
                'is_active': True,
            })
        
        return selling_week
    
    def _get_sale_team(self):
        """Get sale team by POD and branch"""
        HrTeam = self.env['hr.team']
        
        pod = self.to_location_id
        user_branch = self.env.user.employee_id.department_id.branch_id
        
        # Find team where location_ids contains POD and belongs to user's branch
        team = HrTeam.search([
            ('location_ids', 'in', pod.id),
            ('department_id.branch_id', '=', user_branch.id),
        ], limit=1)
        
        if not team:
            # Try to find any team with the POD
            team = HrTeam.search([
                ('location_ids', 'in', pod.id),
            ], limit=1)
        
        return team
    
    def _get_or_create_sea_freight(self, selling_week, team):
        """Find or create ProductTemplateSellingWeek"""
        SeaFreight = self.env['product.template.selling.week']
        
        # Try to find existing sea freight with same week, POL, POD, team
        sea_freight = SeaFreight.search([
            ('selling_week_id', '=', selling_week.id),
            ('from_location_id', '=', self.from_location_id.id),
            ('to_location_id', '=', self.to_location_id.id),
            ('team_id', '=', team.id if team else False),
        ], limit=1)
        
        if not sea_freight:
            sea_freight = SeaFreight.create({
                'goods_info': self.commodity or 'General Cargo',
                'selling_week_id': selling_week.id,
                'from_location_id': self.from_location_id.id,
                'to_location_id': self.to_location_id.id,
                'team_id': team.id if team else False,
            })
        
        return sea_freight
    
    def _create_sea_freight_lines(self, sea_freight):
        """Create sea freight lines from price request response lines"""
        SeaFreightLine = self.env['product.template.selling.week.line']
        
        # Batch search: get all existing lines for this sea freight
        existing_lines = SeaFreightLine.search([
            ('product_template_selling_week_id', '=', sea_freight.id),
        ])
        
        # Build set of existing (shipping_line_id, container_type_id) combinations
        existing_combos = {
            (line.shipping_line_id.id, line.container_type_id.id if line.container_type_id else False)
            for line in existing_lines
        }
        
        # Collect new lines to create
        vals_list = []
        for line in self.request_line_ids:
            combo = (line.shipping_line_id.id, line.container_type_id.id if line.container_type_id else False)
            if combo not in existing_combos:
                vals_list.append({
                    'product_template_selling_week_id': sea_freight.id,
                    'shipping_line_id': line.shipping_line_id.id,
                    'container_type_id': line.container_type_id.id if line.container_type_id else False,
                    'price': line.selling_price or line.price,
                    'currency_id': line.currency_id.id,
                })
        
        # Batch create: insert multi
        if vals_list:
            SeaFreightLine.create(vals_list)
