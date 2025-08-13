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
        domain=lambda self: self._get_user_domain(),
    )
    vehicle_ids = fields.One2many(
        comodel_name='trucking_planning.vehicle',
        inverse_name='branch_id',
        string='vehicles'
    )

    total_users =  fields.Integer(string="Total Users", compute="_compute_total_user", store=False)
    total_vehicles =  fields.Integer(string="Total vehicles", compute="_compute_total_vehicle", store=False)

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

    @api.model
    def _get_user_domain(self):
        allow_users = DepartmentService(self.env).get_user_by_department_type('trucking')

        return [
            ('id', 'in', allow_users.ids),
        ]

    @api.model
    def create(self, vals_list):
        records = super().create(vals_list)
        group = self.env.ref('hp_trucking_planning.group_hp_trucking_planning_member')
        for record in records:
            if record.user_ids:
                group.sudo().write({'users': [(4, user.id) for user in record.user_ids]})
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'user_ids' in vals:
            group = self.env.ref('hp_trucking_planning.group_hp_trucking_planning_member')
            for record in self:
                if record.user_ids:
                    group.sudo().write({'users': [(4, user.id) for user in record.user_ids]})
        return res

    def unlink(self):
        group = self.env.ref('hp_trucking_planning.group_hp_trucking_planning_member')
        for record in self:
            if record.user_ids:
                group.sudo().write({'users': [(3, user.id) for user in record.user_ids]})
        return super().unlink()