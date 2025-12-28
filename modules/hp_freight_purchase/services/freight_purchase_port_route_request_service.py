from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.addons.hp_components.services.request_product_service import RequestProductService
import logging

_logger = logging.getLogger(__name__)

class PortRouteRequestService:
    """Service for handling port route request business logic"""
    
    def __init__(self, env):
        self.env = env

    def action_task_create_new_route(self, wizard):
        """Create a task for new route/port request"""
        wizard.ensure_one()
        
        try:
            # Validate wizard data first
            if not self._validate_wizard_data(wizard):
                raise UserError(_('Please fill in all required fields before creating the task.'))
            
            # Check route exist
            pod_name = ' '.join(wizard.pod_name_request.split())
            pol_name = ' '.join(wizard.pol_name_request.split())
            route_name = f"{pod_name} → {pol_name}"
            route = self.env['route.base'].sudo().search([('name', '=', route_name)], limit=1)
            if route:
                raise UserError(_("Route '%s' already exists.") % route_name)

            # Create task using RequestProductService
            request_product_service = RequestProductService(self.env)
            
            # Create task with port/route information
            task_created = request_product_service.create_task_request_product(
                wizard.sale_order_id,
                pod_name,
                pol_name,
                wizard.etd,
                wizard.container_type_id
            )
            
            if task_created:
                _logger.info(f"Port route request task created successfully for SO: {wizard.sale_order_id.name}")
                
                # Log activity to sale order chatter
                self._log_activity_to_sale_order(wizard)
            
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

    def _validate_wizard_data(self, wizard):
        """Validate wizard data before processing"""
        try:
            errors = []
            
            if not wizard.sale_order_id:
                errors.append("Sale order is required")
                
            if not wizard.pod_name_request:
                errors.append("POD name is required")
                
            if not wizard.pol_name_request:
                errors.append("POL name is required")
                
            if not wizard.container_type_id:
                errors.append("Container type is required")
                
            if not wizard.etd:
                errors.append("ETD is required")
            
            if errors:
                _logger.warning(f"Port route request validation errors: {errors}")
                return False
                
            _logger.info(f"Port route request validation passed for SO: {wizard.sale_order_id.name}")
            return True
            
        except Exception as e:
            _logger.exception(f"Error validating port route request wizard: {e}")
            return False

    def _log_activity_to_sale_order(self, wizard):
        """Log activity to sale order chatter"""
        try:
            # Find the created task
            task = self.env['project.task'].search([
                ('sale_order_id', '=', wizard.sale_order_id.id),
                ('name', 'ilike', f'POD/POL Request for {wizard.sale_order_id.name}')
            ], limit=1, order='create_date desc')
            
            if task:
                activity_message = f"""
                Port/Route Request Task Created
                
                Task: {task.name}
                POD Request: {wizard.pod_name_request}
                POL Request: {wizard.pol_name_request}
                Container Type: {wizard.container_type_id.name if wizard.container_type_id else 'Not specified'}
                ETD: {wizard.etd}
                Task ID: {task.id}
                Created by: {self.env.user.name}
                """
                
                wizard.sale_order_id.message_post(
                    body=activity_message,
                    subject='Port/Route Request Task Created',
                    message_type='comment'
                )
                
                _logger.info(f"Activity logged to sale order chatter for SO: {wizard.sale_order_id.name}")
            
        except Exception as e:
            _logger.exception(f"Error logging activity to sale order: {e}") 