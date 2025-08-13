from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)

class FreightPurchasePortListener(Component):
    _name = 'freight.purchase.port.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.port']

    def on_record_create(self, record, fields=None):
        """Handle port creation - create routes and products"""
        self._create_routes_and_products(record)

    def on_record_write(self, record, fields=None):
        """Handle port updates - update routes and products when name or is_local changes"""
        if fields and ('name' in fields or 'is_local' in fields):
            self._update_routes_and_products(record)
            if 'is_local' in fields:
                self._update_route_directions(record)

    def _create_routes_and_products(self, port):
        """
        Create routes and product templates for the new port with all existing ports.
        Optimized with bulk creation for better performance.
        """
        try:
            other_ports = self.env['freight.purchase.port'].search([
                ('id', '!=', port.id),
                ('is_active', '=', True)
            ])
            
            Route = self.env['freight.purchase.route']
            
            # Prepare all route data for bulk creation
            route_vals_list = []
            
            for other_port in other_ports:
                # Check if routes already exist to avoid duplicates
                existing_route_pol_to_pod = Route.search([
                    ('pol_id', '=', port.id),
                    ('pod_id', '=', other_port.id)
                ], limit=1)
                
                existing_route_pod_to_pol = Route.search([
                    ('pol_id', '=', other_port.id),
                    ('pod_id', '=', port.id)
                ], limit=1)
                
                # Only create routes if they don't exist and ports have different is_local values
                if not existing_route_pol_to_pod and port.is_local != other_port.is_local:
                    # Determine direction for route from this port to other port
                    direction = 'N/A'
                    if other_port.is_local:  # POD is local
                        direction = 'import'
                    elif port.is_local:  # POL is local
                        direction = 'export'
                    
                    route_vals_list.append({
                        'pol_id': port.id,
                        'pod_id': other_port.id,
                        'is_active': True,
                        'direction': direction,
                    })
                
                if not existing_route_pod_to_pol and port.is_local != other_port.is_local:
                    # Determine direction for route from other port to this port
                    direction = 'N/A'
                    if port.is_local:  # POD is local
                        direction = 'import'
                    elif other_port.is_local:  # POL is local
                        direction = 'export'
                    
                    route_vals_list.append({
                        'pol_id': other_port.id,
                        'pod_id': port.id,
                        'is_active': True,
                        'direction': direction,
                    })
            
            # Bulk create all routes at once
            if route_vals_list:
                created_routes = Route.create(route_vals_list)
                
                # Create product templates for all created routes
                for route in created_routes:
                    self._create_product_template(route)
                    
        except Exception as e:
            _logger.exception(f"Error creating routes and products for port {port.name}: {e}")

    def _create_product_template(self, route):
        """
        Create a product template for the given route.
        """
        try:
            Product = self.env['product.template']
            
            # Check if product already exists for this route
            existing_product = Product.search([
                ('route_id', '=', route.id),
                ('type', '=', 'pricing')
            ], limit=1)
            
            if not existing_product:
                Product.with_context(create_from_route=True).create({
                    'type': 'pricing',
                    'route_id': route.id,
                    'name': route.name,
                    'categ_id': self.env.ref('product.product_category_all').id,
                    'uom_id': self.env.ref('uom.product_uom_unit').id,
                    'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                    'project_id': False,
                    'project_template_id': False,
                })
                
        except Exception as e:
            _logger.exception(f"Error creating product template for route {route.name}: {e}")

    def _update_routes_and_products(self, port):
        """
        Update routes and related products when port name changes.
        """
        try:
            Route = self.env['freight.purchase.route']
            Product = self.env['product.template']
            
            # Find all routes that use this port (as POL or POD)
            routes_as_pol = Route.search([('pol_id', '=', port.id)])
            routes_as_pod = Route.search([('pod_id', '=', port.id)])
            
            all_routes = routes_as_pol + routes_as_pod
            
            for route in all_routes:
                # Update related products
                products = Product.search([('route_id', '=', route.id)])
                if products:
                    products.write({'name': route.name})
                    
        except Exception as e:
            _logger.exception(f"Error updating routes and products for port {port.name}: {e}")

    def _update_route_directions(self, port):
        """
        Update direction for all routes involving this port when is_local changes.
        """
        try:
            Route = self.env['freight.purchase.route']
            
            # Find all routes that use this port (as POL or POD)
            routes_as_pol = Route.search([('pol_id', '=', port.id)])
            routes_as_pod = Route.search([('pod_id', '=', port.id)])
            
            all_routes = routes_as_pol + routes_as_pod
            
            for route in all_routes:
                # Skip routes with manual direction
                if route.direction_manual:
                    continue
                    
                # Recompute direction based on current port is_local values
                direction = 'N/A'
                if route.pod_id.is_local:
                    direction = 'import'
                elif route.pol_id.is_local:
                    direction = 'export'
                
                route.write({'direction': direction})
                    
        except Exception as e:
            _logger.exception(f"Error updating route directions for port {port.name}: {e}") 