from odoo import models


class UserServiceInheritService(models.AbstractModel):
    _inherit = 'hp_components.user.service'

    def get_sale_teams_by_user(self, user_id=None):
        """Get sale teams associated with the given user (or current user if none provided)."""
        if user_id is None:
            user = self.env.user
        else:
            user = self.env['res.users'].browse(user_id)

        return self.env['sale.team'].search([('member_ids', 'in', user.id)])