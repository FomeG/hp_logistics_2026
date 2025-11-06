from odoo import models, fields, api

class HrTeam(models.Model):
    _name = 'hr.team'
    _description = 'HR Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Team Name",
        required=True,
        tracking=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        tracking=True
    )
    user_ids = fields.Many2many(
        'res.users',
        'hr_team_user_rel',
        'team_id', 'user_id',
        string="Members",
        tracking=True,
        domain="[('id', 'in', available_user_ids)]"
    )

    available_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_available_user_ids',
        store=False
    )

    @api.depends('department_id')
    def _compute_available_user_ids(self):
        for record in self:
            if record.department_id:
                employees = self.env['hr.employee'].search([
                    ('department_id', '=', record.department_id.id),
                    ('user_id', '!=', False)
                ])
                record.available_user_ids = employees.mapped('user_id')
            else:
                record.available_user_ids = self.env['res.users'].search([])
        
    @api.constrains('user_ids', 'department_id')
    def _check_users_department(self):
        for record in self:
            if record.department_id and record.user_ids:
                employees = self.env['hr.employee'].search([
                    ('department_id', '=', record.department_id.id)
                ])
                valid_user_ids = employees.mapped('user_id').ids
                
                invalid_users = record.user_ids.filtered(lambda u: u.id not in valid_user_ids)
                if invalid_users:
                    raise models.ValidationError(
                        f"The following users are not in the selected department: "
                        f"{', '.join(invalid_users.mapped('name'))}"
                    )