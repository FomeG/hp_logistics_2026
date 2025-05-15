from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HpDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    TYPE_SALE = 'sale'
    TYPE_PRICING = 'pricing'
    TYPE_TRUCKING = 'trucking'

    department_type = fields.Selection([
        (TYPE_SALE, 'Sale'),
        (TYPE_PRICING, 'Pricing'),
        (TYPE_TRUCKING, 'Trucking'),
    ], string='Department Type', required=True)

    def write(self, vals):
        for record in self:
            if 'department_type' in vals:
                if record.department_type:
                    raise UserError(_("You cannot modify the Department Type once it's set."))
        return super(HpDepartmentInherit, self).write(vals)

    def unlink(self):
        for department in self:
            employees = self.env['hr.employee'].search([('department_id', '=', department.id)])
            if employees:
                raise UserError(
                    _("Cannot delete department '%s' because there are still employees in this department..") % department.name
                )
        return super().unlink()