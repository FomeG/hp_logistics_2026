from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from ...hp_components.services.activity_service import ActivityService
from ...hp_components.services.department_service import DepartmentService

class HrLeaveInherit(models.Model):
    _inherit = 'hr.leave'

    request_refuse = fields.Boolean(string='Request Refuse', default=False)


    def action_request_refuse(self):
        self.sudo().write({
            'request_refuse': True,
        })
        return True
    
    def _handle_record_write(self):
        if not self.create_uid:
            return False

        service = ActivityService(
            env=self.env,
            model_name='hr.leave',
            record_id=self.id,
            user_ids=self.create_uid.id
        )
        service._create_activity_by_type(
            summary= f"Your leave request has been {self.state}",
            note=''
        )
    
        return True