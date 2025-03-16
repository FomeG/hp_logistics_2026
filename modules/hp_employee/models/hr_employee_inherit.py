from odoo import models, _
from odoo.exceptions import ValidationError

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'
    
    def action_create_user_full(self):
      self.ensure_one()
      if self.user_id:
          raise ValidationError(_("This employee already has an user."))
      return {
            'name': _('Create User'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'form',
            'view_id': self.env.ref('base.view_users_form').id,
            'target': 'new',
            'context': dict(self._context, **{
                'default_create_employee_id': self.id,
                'default_name': self.name,
                'default_phone': self.work_phone,
                'default_mobile': self.mobile_phone,
                'default_login': self.work_email,
                'default_partner_id': self.work_contact_id.id,
          })
      }
