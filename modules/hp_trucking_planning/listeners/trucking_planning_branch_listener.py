from odoo.addons.component.core import Component
from odoo import fields

class BranchUserListener(Component):
    _name = 'trucking_planning.branch_user_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.branch']

    def _update_user_group(self, records):
        group = self.env.ref('hp_trucking_planning.group_hp_trucking_planning_member').sudo()
        all_branch_users = self.env['trucking_planning.branch'].search([]).mapped('user_ids')
        current_group_users = group.users
        users_to_add = all_branch_users - current_group_users
        if users_to_add:
            group.write({'users': [(4, user.id) for user in users_to_add]})
        users_to_remove = current_group_users - all_branch_users
        if users_to_remove:
            group.write({'users': [(3, user.id) for user in users_to_remove]})

    def on_record_create(self, record, fields=None):
        if 'user_ids' in fields:
            self._update_user_group(record)

    def on_record_write(self, record, fields=None):
        if 'user_ids' in fields:
            self._update_user_group(record)

    def on_record_unlink(self, record):
        self._update_user_group(record)