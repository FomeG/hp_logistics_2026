from odoo import models, fields, _
from odoo.exceptions import UserError

class ProjectTaskTypeInherit(models.Model):
    _inherit = 'project.task.type'

    PROTECTED_STAGES = {'Open', 'In Progress', 'Review', 'Done', 'Pending'}

    def unlink(self):
        for record in self:
            if record.name in self.PROTECTED_STAGES:
                projectProtected = self.env['project.project'].PROTECTED_TYPE
                isTaskTypeProtected = self.env['project.project'].search([
                    ('type', 'in', list(projectProtected)),
                    ('type_ids', 'in', record.ids)
                ])
                if isTaskTypeProtected:
                    raise UserError(_("You cannot delete the stage '%s' because it is used in a protected project.") % record.name)
        return super().unlink()