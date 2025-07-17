from .base_task_service import BaseTaskService
import logging
from .department_service import DepartmentService
from .project_service import ProjectService
from .request_price_service import RequestPriceService
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import _

_logger = logging.getLogger(__name__)


class RequestProductService(BaseTaskService):
    _name = 'custom_component.product.request.task'

    def __init__(self,env):
        self.env = env
        super().__init__(env)
        self.department_service = DepartmentService(env)
        self.project_service = ProjectService(env)
        self.request_price_service = RequestPriceService(env)

    def create_task_request_product(self, sale_order, pod_name, pol_name, etd, container_type):
        project = self.project_service.get_project_by_type(ProjectService.PROJECT_TYPE_PRODUCT_REQUEST)
        leader = self.department_service.get_pricing_department_leader()
        leader = leader if leader else self.env.user
        _logger.info(f'Start creating task for sale_order_id: {sale_order.id}, sale_order_name: {sale_order.name}')
        
        if not project:
            _logger.error(f'Project not found for type: {ProjectService.PROJECT_TYPE_PRODUCT_REQUEST}')
            return False
            
        if not leader:
            _logger.error('No leader found for pricing department')
            return False
            
        try:
            
            task_vals = {
                'name': f'POD/POL Request for {sale_order.name}',
                'project_id': project.id,
                'sale_order_id': sale_order.id,
                'user_ids': [leader.id],
                'etd': etd,
                'pod_name_request': pod_name,
                'pol_name_request': pol_name,
                'container_type_id': container_type.id,
                'date_assign': datetime.now(),
            }
            task = self.env['project.task'].sudo().create(task_vals)

            # Try to force set sale_order_id if it's not set
            if not task.sale_order_id:
                _logger.info('Attempting to force set sale_order_id via write')
                task.write({'sale_order_id': sale_order.id})
                _logger.info(f'After write - Task sale_order_id: {task.sale_order_id}, sale_order_id.id: {task.sale_order_id.id if task.sale_order_id else "None"}')

            _logger.info(f'Created task for sale_order: {task.sale_order_id.name if task.sale_order_id else "None"}')
            
            return True
            
        except Exception as e:
            _logger.exception(f'Error creating task: {e}')
            return False
    
    def handle_approve_product(self, task):
        self.validate_approve_product(task)

        pol = self.create_port_by_name(task.pol_name_request, task.region_pol_id.id, False)
        pod = self.create_port_by_name(task.pod_name_request, task.region_pod_id.id, False)
        
        # Find the route that was automatically created by the listener
        route = self.env['freight.purchase.route'].sudo().search([
            ('pol_id', '=', pol.id), 
            ('pod_id', '=', pod.id)
        ], limit=1)
        
        if not route:
            raise ValidationError(f"Route not found for POL {pol.name} and POD {pod.name}. Please check if ports were created correctly.")
        
        # Find the product that was automatically created for this route
        new_product = self.env['product.template'].sudo().search([
            ('route_id', '=', route.id),
            ('type', '=', 'pricing')
        ], limit=1)
        
        if not new_product:
            raise ValidationError(f"Product not found for route {route.name}. Please check if product was created correctly.")

        sale_order = task.sale_order_id
        new_sale_order_line = self.env['sale.order.line'].sudo().create({
            'name': route.name,
            'order_id': sale_order.id,
            'product_id': new_product.product_variant_id.id,
            'container_type_id': task.container_type_id.id,
            'product_uom_qty': 1.0,
            'name': new_product.name,
            'product_type_filter': 'pricing'
        })

        self.request_price_service.create_request_price_task(new_sale_order_line, task.etd)
        # Use context to prevent duplicate price request task creation
        sale_order.sudo().with_context(skip_price_request_listener=True).write({'state': 'activated'})
        task.update_done_task(pod.id, pol.id)
        return True

    def create_port_by_name(self, port_name, region_id, is_local):
        domain = [
            ('name', 'ilike', port_name),
            ('region_id', '=', region_id),
            ('is_local', '=', is_local),
        ]
        port = self.env['freight.purchase.port'].sudo().search(domain, limit=1)
        if not port:
            port = self.env['freight.purchase.port'].sudo().create({
                'name': port_name,
                'region_id': region_id,
                'is_local': is_local,
                'is_active': True,
            })
        return port
    
    # def create_route_by_pol_pod(self, pol, pod):
    #     route = self.env['freight.purchase.route'].sudo().search([('pod_id', '=', pod.id), ('pol_id', '=', pol.id)], limit=1)
    #     if not route:
    #         route = self.env['freight.purchase.route'].sudo().create({
    #             'pol_id': pol.id,
    #             'pod_id': pod.id,
    #             'is_active': True,
    #         })
    #     return route
    
    def validate_approve_product(self, task):
        if not task.sale_order_id:
            raise ValidationError(_("Quotation is required."))
        if not task.pod_name_request:
            raise ValidationError(_("POD name is required."))
        if not task.pol_name_request:
            raise ValidationError(_("POL name is required."))
        if not task.region_pod_id:
            raise ValidationError(_("Region POD is required."))
        if not task.region_pol_id:
            raise ValidationError(_("Region POL is required."))
        if not task.container_type_id:
            raise ValidationError(_("Container type is required."))
