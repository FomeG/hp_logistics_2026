from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_components.services.task_service import TaskService

import logging
_logger = logging.getLogger(__name__)

class PortRouteRequestWizard(models.TransientModel):
    _name = 'port.route.request.wizard'
    _description = 'Port/Route Request Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    # sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    etd = fields.Date(string="ETD", required=True, default=fields.Date.today())
    pod_name_request = fields.Char('POD (Port of Discharge) name request', required=True)
    pol_name_request = fields.Char('POL (Port of Loading) name request', required=True)
    container_type_id = fields.Many2one(
        'container.type',
        string="Container Type (For this quotation)",
        required=True,
        default=lambda self: self.env['container.type'].search([('name', '=', '20DC')], limit=1)
    )
    notes = fields.Text('Additional Notes')

    def action_task_create_new_route(self):
        """Create a task for new route/port request"""
        self.ensure_one()
        
        try:
            # Create task using TaskService
            service = TaskService(self.env)
            project = service.get_project_by_type(TaskService.PROJECT_TYPE_PRODUCT_REQUEST)
            
            if not project:
                raise UserError(_('No project found for product requests. Please configure the project first.'))
            
            # Create task with port/route information
            task = service.create_task_by_sale_order(
                'pricing',
                project.id, 
                TaskService.TASK_TYPE_PRODUCT_REQUEST, 
                self.sale_order_id,
                {
                    'etd': self.etd,
                    'pod_name_request': self.pod_name_request,
                    'pol_name_request': self.pol_name_request,
                    'container_type_id': self.container_type_id.id,
                    # 'sale_order_line_id': self.sale_order_line_id.id if self.sale_order_line_id else False,
                    'notes': self.notes
                }
            )
            
            # Show success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Task Created'),
                    'message': _('Port/Route Request task created successfully!'),
                    'sticky': False,
                    'type': 'success',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
            
        except Exception as e:
            _logger.exception(f"Error creating port/route request task: {e}")
            raise UserError(_('Failed to create task. Please try again or contact support.'))