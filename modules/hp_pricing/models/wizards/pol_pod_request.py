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
    volume_cont = fields.Selection([
        ('20DC', '20DC'),
        ('20RF', '20RF'),
        ('20OT', '20OT'),
        ('20HC', '20HC'),
        ('40DC', '40DC'),
        ('40HC', '40HC'),
        ('40HQ', '40HQ'),
        ('40RF', '40RF'),
        ('40HCRF', '40HCRF'),
        ('40OT', '40OT'),
    ], string="Container Type (For this quotation)", default='20DC')

    def action_task_create_new_sealine(self):
        self.ensure_one()
        service = TaskService(self.env)
        project = service.get_project_by_type(TaskService.PROJECT_TYPE_PRODUCT_REQUEST)
        service.create_task_by_sale_order('pricing', project.id, TaskService.TASK_TYPE_PRODUCT_REQUEST, self.sale_order_id, self.etd, self.pod_name_request, self.pol_name_request, self.volume_cont)

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