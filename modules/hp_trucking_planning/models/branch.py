from odoo import models, fields, api
from ...hp_components.services.department_service import DepartmentService

class Branch(models.Model):
    _name = 'trucking_planning.branch'
    _description = 'Branch'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
    )
    plan_prefix = fields.Char(
        string="Plan Prefix",
        required=True,
        tracking=True,
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string="User",
    )
    vehicle_ids = fields.One2many(
        comodel_name='trucking_planning.vehicle',
        inverse_name='branch_id',
        string='vehicles'
    )

    total_users =  fields.Integer(string="Total Users", compute="_compute_total_user", store=False)
    total_vehicles =  fields.Integer(string="Total vehicles", compute="_compute_total_vehicle", store=False)
    allow_user_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_allow_user_ids',
        store=False
    )
    
    _sql_constraints = [
        ('unique_plan_prefix', 'UNIQUE(plan_prefix)','Plan prefix must be unique!'),
    ]
    

    @api.depends('user_ids')
    def _compute_total_user(self):
        for rec in self:
            rec.total_users = len(rec.user_ids)

    @api.depends('vehicle_ids')
    def _compute_total_vehicle(self):
        for rec in self:
            rec.total_vehicles = len(rec.vehicle_ids)

    @api.depends('name')
    def _compute_allow_user_ids(self):
        service = DepartmentService(self.env)
        for rec in self:
            rec.allow_user_ids = service.get_user_by_department_type('trucking')