from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_pricing.models.inherit_res_users import get_excluded_user_ids
from odoo.addons.hp_employee.models.hr_department_inherit import HpDepartmentInherit
from odoo.addons.hp_components.services.task_service import TaskService

import logging
_logger = logging.getLogger(__name__)
class PodPolRequestWizard(models.TransientModel):
    _name = 'pod.pol.request.wizard'
    _description = 'POD/POL Request Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    etd = fields.Date(string="ETD", required=True, default=fields.Date.today())
    pod_name_request = fields.Char('POD name request', required=True)
    pol_name_request = fields.Char('POL name request', required=True)

    def action_task_create_new_sealine(self):
        self.ensure_one()
        service = TaskService(self.env)
        project = service.get_project_by_type(TaskService.PROJECT_TYPE_PRODUCT_REQUEST)
        service.create_task_by_sale_order('pricing', project.id, TaskService.TASK_TYPE_PRODUCT_REQUEST, self.sale_order_id, self.etd, self.pod_name_request, self.pol_name_request)

        # project = self.env['project.project'].search([('type', '=', 'request_product')], limit=1)
        #
        # if not project:
        #     raise UserError(_("No project found with type 'request_product'. Please create it first."))
        #
        # # Create task with the collected information
        # task_vals = {
        #     'name': f'POD/POL Request for {self.sale_order_id.name}',
        #     'project_id': project.id,
        #     'sale_order_id': self.sale_order_id.id,
        #     'etd': self.etd,
        #     'pod_name_request': self.pod_name_request,
        #     'pol_name_request': self.pol_name_request,
        # }
        #
        # # Get list of users to exclude
        # # excluded_ids = get_excluded_user_ids(self.env)
        # pricing_managers = self.env['hr.department']._get_manage_user_by_type('pricing')
        #
        # _logger.info((f"pricing manager ids: {pricing_managers}"))
        #
        # pricing_director_group = self.env.ref('hp_pricing.group_hp_pricing_director')
        # pricing_director = self.env['res.users'].search([
        #     ('groups_id', 'in', pricing_director_group.id),
        #     # ('id', 'not in', excluded_ids),
        #     ('id', 'in', pricing_managers.ids),
        #     ('active', '=', True)
        # ], limit=1)
        #
        # assignee_ids = []
        #
        # if pricing_director:
        #     assignee_ids.append(pricing_director.id)
        #
        # # Add assignees if found
        # if assignee_ids:
        #     task_vals['user_ids'] = [(6, 0, assignee_ids)]
        #
        # self.env['project.task'].sudo().create(task_vals)

        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Task Created'),
                'message': _('POD/POL Request task created successfully!'),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }