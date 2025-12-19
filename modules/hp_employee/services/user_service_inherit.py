from odoo import models, api


class UserServiceInherit(models.AbstractModel):
    _name = 'hp_employee.user.service'
    _inherit = 'hp_components.user.service'
    _description = 'User Service Inherit'

    @api.model
    def get_user_teams(self, user=None):
        user = user or self.env.user
        return self.env['hr.team'].search([
            ('user_ids', 'in', user.id)
        ])

    @api.model
    def inject_user_teams_domain(self, domain=None, user=None):
        domain = list(domain or [])
        teams = self.get_user_teams(user)
        if not teams:
            if super().is_admin_user(user):
                return domain
        domain.append(('team_id', 'in', teams.ids))
        return domain

