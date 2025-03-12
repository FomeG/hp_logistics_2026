from odoo import models, _
from odoo.exceptions import UserError

class HpDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    def unlink(self):
        for department in self:
            employees = self.env['hr.employee'].search([('department_id', '=', department.id)])
            if employees:
                raise UserError(
                    _("Cannot delete department '%s' because there are still employees in this department..") % department.name
                )
        return super().unlink()