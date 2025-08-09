from odoo import models, fields, api
from ...hp_components.services.department_service import DepartmentService
from ..services.planning_service import planning_service

class Plan(models.Model):
    _name = 'trucking_planning.plan'
    _description = 'Plan'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'date asc'

    name = fields.Char(
        string="Name",
        readonly=True,
        tracking=True,
    )
    date = fields.Date(
        string='Return Shipment Date',
        required=True,
        index=True,
        tracking=True,
    )
    month = fields.Integer(
        string='Month',
        compute='_compute_month_year',
        store=True,
        readonly=True,
    )
    year = fields.Integer(
        string='Year',
        compute='_compute_month_year',
        store=True,
        readonly=True,
    )
    vehicle_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain="[('type', '=', 'truck')]",
        index=True,
    )
    driver_id = fields.Many2one(
        related='vehicle_id.primary_driver_id',
        store=False,
    )
    status = fields.Selection([
            ('active', 'Active'),
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('cancelled', 'Cancelled'),
        ],
        default='active',
        required=True,
        string="Status",
        tracking=True,
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        inverse_name='plan_id',
    )
    total_trips = fields.Char(
        string="Total Trips",
        compute='_compute_total_trips',
        store=False
    )

    @api.depends('date')
    def _compute_month_year(self):
        for record in self:
            if record.date:
                record.month = record.date.month
                record.year = record.date.year
            else:
                record.month = False
                record.year = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                user = self.env.user
                branch = self.env['trucking_planning.branch'].search([
                    ('user_ids', 'in', [user.id]),
                ], limit=1)
                prefix = branch.plan_prefix if branch else 'PLAN'
                today = fields.Date.today().strftime('%Y%m%d')
                seq_number = self.env['ir.sequence'].next_by_code('trucking_planning.plan')
                vals['name'] = f"{prefix}/{today}/{seq_number}"

        records = super().create(vals_list)
        for record in records:
            if record.vehicle_id and record.date:
                record.with_delay().remove_vehicle_driver_of_plan_and_plan_line(
                    vehicle_id=record.vehicle_id.id,
                    date_plan=record.date,
                    exclude_plan_id=record.id
                )
    
        return records
    
    def write(self, vals):
        result = super().write(vals)

        if 'vehicle_id' in vals or 'date' in vals:
            for record in self:
                if record.vehicle_id and record.date:
                    record.with_delay().remove_vehicle_driver_of_plan_and_plan_line(
                        vehicle_id=record.vehicle_id.id,
                        date_plan=record.date,
                        exclude_plan_id=record.id
                    )
    
        return result

    @api.depends('plan_line_ids')
    def _compute_total_trips(self):
        for record in self:
            record.total_trips = "0 Trip(s)"
            if record.plan_line_ids:
                record.total_trips = f"{len(record.plan_line_ids)} Trip(s)"

    def action_view_trips(self):
        self.ensure_one()
        return {
            'name': 'Trips',
            'res_model': 'trucking_planning.plan.line',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {
                'default_plan_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def remove_vehicle_driver_of_plan_and_plan_line(self, vehicle_id, date_plan, exclude_plan_id):
        planning_service(self.env).remove_vehicle_driver_by_vehicle_and_date_plan(vehicle_id, date_plan, exclude_plan_id)
