from odoo import models, fields, api
from ...hp_components.services.department_service import DepartmentService

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                user = self.env.user
                rule = self.env['trucking_planning.plan.prefix.rule'].search([
                    ('user_ids', 'in', [user.id]),
                ], limit=1)
                prefix = rule.name if rule else 'PLAN'
                today = fields.Date.today().strftime('%Y%m%d')
                seq_number = self.env['ir.sequence'].next_by_code('trucking_planning.plan')
                vals['name'] = f"{prefix}/{today}/{seq_number}"
        return super().create(vals_list)

    @api.depends('plan_line_ids')
    def _compute_total_trips(self):
        for record in self:
            record.total_trips = "0 Trip(s)"
            if record.plan_line_ids:
                record.total_trips = f"{len(record.plan_line_ids)} Trip(s)"
