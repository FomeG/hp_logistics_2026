from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ...hp_components.models.constants import DepartmentTypeCode
from ...hp_components.services.department_service import DepartmentService
from ...hp_components.services.activity_service import ActivityService

class FreightRequestInherit(models.Model):
    _inherit = 'freight.purchase.sea.freight.request'

    def _update_assignee(self):
        creator_branch_id = self.create_uid.employee_id.department_id.branch_id.id
        pricing_manager = DepartmentService(self.env).get_department_manager_by_type_and_branch(DepartmentTypeCode.PRICING, creator_branch_id)

        team = self.env['hr.team'].sudo().search([
            ('location_ids', 'in', self.to_location_id.id),
            ('department_id.department_type_id.code', '=', DepartmentTypeCode.PRICING),
        ], limit=1)

        if team and team.user_ids:
            assignee_id = team.user_ids[:1].id
            notify_ids = [assignee_id]
            if pricing_manager:
                notify_ids.append(pricing_manager.id)
            self._handle_notify_for_pricing(notify_ids)
            # self._handle_notify_for_pricing([assignee_id, pricing_manager.id])
        elif pricing_manager:
            assignee_id = pricing_manager.id
            self._handle_notify_for_pricing([pricing_manager.id])
        else:
            # No team users and no pricing manager found, skip update
            return

        self.write({
            'assignee_id': assignee_id,
        })

    def _handle_notify_for_pricing(self, user_ids):
        if not self.assignee_id:
            return False

        service = ActivityService(
            env=self.env,
            model_name='freight.purchase.sea.freight.request',
            record_id=self.id,
            user_ids=user_ids
        )

        service._create_activity_by_type(
            summary=f"New price request for {self.from_location_id.name} - {self.to_location_id.name}",
            note=''
        )

        return True




    def action_assign_pricing_member(self):
        """Open wizard to assign price request to a pricing member"""
        self.ensure_one()
        return {
            'name': _('Assign Price Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'assign.price.request.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_sale.view_assign_price_request_wizard_form').id,
            'target': 'new',
            'context': {
                'default_price_request_id': self.id,
            },
        }