from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_components.services.department_service import DepartmentService

class MassAssignSaleUserWizard(models.TransientModel):
    _name = 'res.partner.client.assign.sale.wizard'
    _description = 'Bulk Assign Sale Branch to Client'

    client_ids = fields.Many2many(
        'res.partner.client',
        string='Selected Clients',
        readonly=True
    )
    branch_id = fields.Many2one(
        'hr.branch',
        string='Assign Branch',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            defaults['client_ids'] = [(6, 0, self.env.context['active_ids'])]
        if 'branch_id' in fields_list and not defaults.get('branch_id'):
            defaults['branch_id'] = self.env.user.branch_ids[:1].id
        return defaults

    def action_assign_sale_branch(self):
        self.ensure_one()
        if not self.client_ids:
            raise UserError(_('No clients selected.'))
        if not self.branch_id:
            raise UserError(_('Please select a branch.'))

        update_vals = {
            'branch_id': self.branch_id.id,
        }
        self.client_ids.write(update_vals)
        updated_count = len(self.client_ids)

        message = _('Successfully updated %s Sale branch with client "%s".') % (
            updated_count, self.branch_id.name
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Branch Assignment Successful'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }