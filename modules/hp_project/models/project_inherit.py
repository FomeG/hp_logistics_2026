from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv.expression import AND

class ProjectInherit(models.Model):
    _inherit = 'project.project'

    REQUEST_PRICE = 'request_price'
    REQUEST_PRODUCT = 'request_product'
    ASSIGN_BOOKING = 'assign_booking'
    APPROVE_QUOTATION = 'approve_quotation'

    PROTECTED_TYPE = {REQUEST_PRICE, REQUEST_PRODUCT, ASSIGN_BOOKING, APPROVE_QUOTATION}

    type = fields.Char(string="Type")

    def unlink(self):
        for record in self:
            if record.type in self.PROTECTED_TYPE:
                raise UserError(_("You cannot delete this this project."))
        return super().unlink()
    
    def _compute_open_task_count(self):
        current_user = self.env.user
        additional_domain = [
            ('state', 'in', self.env['project.task'].OPEN_STATES),
            ('user_ids', 'in', [current_user.id]),
        ]
        count_field = 'open_task_count'
        count_fields = {fname for fname in self._fields if 'count' in fname}
        if count_field not in count_fields:
            raise ValueError(f"Parameter 'count_field' can only be one of {count_fields}, got {count_field} instead.")
        domain = [('project_id', 'in', self.ids), ('display_in_project', '=', True)]
        if additional_domain:
            domain = AND([domain, additional_domain])
        tasks_count_by_project = dict(self.env['project.task'].with_context(
            active_test=any(project.active for project in self)
        )._read_group(domain, ['project_id'], ['__count']))
        for project in self:
            project.update({count_field: tasks_count_by_project.get(project, 0)})
    