from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_components.services.task_service import TaskService
from odoo.addons.hp_components.services.request_product_service import RequestProductService
from odoo.addons.hp_components.services.project_service import ProjectService

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
            request_product_service = RequestProductService(self.env)
            
            # Create task with port/route information
            task = request_product_service.create_task_request_product(
                self.sale_order_id,
                self.pod_name_request,
                self.pol_name_request,
                self.etd,
                self.container_type_id
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