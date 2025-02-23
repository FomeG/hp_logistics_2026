from odoo import models, fields, api

class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    position = fields.Selection([
        ('sale', 'Sale'),
        ('pricing', 'Pricing'),
        ('cs', 'Customer Service'),
        ('trucking', 'Trucking'),
        ('ops', 'Operations'),
        ('accounting', 'Accounting')
    ], string="Position")

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._update_group_by_position()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'position' in vals:
            self._update_group_by_position()
        return res

    def _update_group_by_position(self):
        position_mapping = {
            'sale': self.env.ref('hp_user.position_group_sale'),
        }
        custom_group_ids = [group.id for group in position_mapping.values()]
        
        for user in self:
            removal_commands = [(3, group_id, False) for group_id in custom_group_ids]
            user.write({'groups_id': removal_commands})
            
            if user.position in position_mapping:
                user.write({'groups_id': [(4, position_mapping[user.position].id, False)]})