from odoo import fields, models, api
from odoo.exceptions import UserError


class ResUsers(models.Model):
    """
    Model to handle hiding specific menu items and restricting app access.
    """
    _inherit = 'res.users'

    def write(self, vals):
        """
        Write method for the ResUsers model.
        """
        res = super(ResUsers, self).write(vals)
        if 'hide_menu_ids' in vals:
            for record in self:
                # This part handles the original menu hiding feature
                previous_menus = self.env['ir.ui.menu'].search([('restrict_user_ids', 'in', [record.id])])
                
                # Add new restrictions
                for menu in record.hide_menu_ids:
                    menu.write({'restrict_user_ids': [fields.Command.link(record.id)]})
                
                # Remove old restrictions
                removed_menus = previous_menus - record.hide_menu_ids
                for menu in removed_menus:
                    menu.write({'restrict_user_ids': [fields.Command.unlink(record.id)]})
        return res

    def _get_allowed_apps_groups(self):
        """Get the groups that should be allowed for regular users."""
        allowed_group_ids = []

        # This logic was flawed and hid the Sales app, as you remember
        sales_groups = self.env['res.groups'].search([
            ('category_id.name', '=', 'Sales')
        ])
        allowed_group_ids.extend(sales_groups.ids)

        # hp_freight_purchase related groups
        freight_groups = self.env['res.groups'].search([
            ('category_id.name', 'ilike', 'Freight')
        ])
        allowed_group_ids.extend(freight_groups.ids)

        # Essential base groups that should always be kept
        essential_groups = ['base.group_user', 'base.group_portal', 'base.group_public']
        for xml_id in essential_groups:
            group = self.env.ref(xml_id, raise_if_not_found=False)
            if group:
                allowed_group_ids.append(group.id)
                
        return allowed_group_ids

    def restrict_user_access(self):
        """
        Restrict user access to only Sales and hp_freight_purchase apps.
        """
        for user in self:
            if user.has_group('base.group_system'):
                continue # Skip admins

            allowed_groups = self.env['res.groups'].browse(user._get_allowed_apps_groups())
            current_groups = user.groups_id
            
            # This is a simplified removal logic from that version
            groups_to_remove = self.env['res.groups'].search([
                ('id', 'not in', allowed_groups.ids),
                ('id', 'in', current_groups.ids)
            ])
            
            if groups_to_remove:
                user.write({'groups_id': [(3, group.id) for group in groups_to_remove]})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'User access has been restricted.',
                'type': 'success',
            }
        }

    def _get_is_admin(self):
        """
        Compute method to check if the user is an admin.
        """
        for rec in self:
            rec.is_admin = rec.has_group('base.group_system')

    hide_menu_ids = fields.Many2many(
        'ir.ui.menu', string="Hidden Menu",
        store=True, help='Select menu items that need to '
                         'be hidden to this user.')
    is_admin = fields.Boolean(compute=_get_is_admin, string="Is Admin",
                              help='Check if the user is an admin.')


class IrUiMenu(models.Model):
    """
    Model to restrict the menu for specific users.
    """
    _inherit = 'ir.ui.menu'

    restrict_user_ids = fields.Many2many(
        'res.users', string="Restricted Users",
        help='Users restricted from accessing this menu.')
