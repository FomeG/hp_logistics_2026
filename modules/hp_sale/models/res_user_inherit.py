from odoo import models

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _default_groups(self):
        default_user = self.env.ref('base.default_user', raise_if_not_found=False)
        groups = default_user.sudo().groups_id if default_user else self.env['res.groups']
        product_creation_group = self.env.ref('product.group_product_manager', raise_if_not_found=False)
        if product_creation_group:
            groups = groups - product_creation_group
        return groups
