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
        """Handle port updates - update routes and products when name changes"""
        if fields and 'name' in fields:
            self._update_routes_and_products(record)

    def _create_routes_and_products(self, port):
        """
        Create routes and product templates for the new port with all existing ports.
        Migrated from port model logic.
        """
        try:
            other_ports = self.env['freight.purchase.port'].search([
                ('id', '!=', port.id),
                ('is_active', '=', True)
            ])
            
            Route = self.env['freight.purchase.route']
            
            for other_port in other_ports:
                # Create route from this port to other port (as POL -> POD)
                route_pol_to_pod = Route.search([
                    ('pol_id', '=', port.id),
                    ('pod_id', '=', other_port.id)
                ], limit=1)
                
                if not route_pol_to_pod:
                    route_pol_to_pod = Route.create({
                        'pol_id': port.id,
                        'pod_id': other_port.id,
                        'is_active': True,
                    })
                    
                    # Create product template for this route
                    self._create_product_template(route_pol_to_pod)
                
                # Create route from other port to this port (as POL -> POD)
                route_pod_to_pol = Route.search([
                    ('pol_id', '=', other_port.id),
                    ('pod_id', '=', port.id)
                ], limit=1)
                
                if not route_pod_to_pol:
                    route_pod_to_pol = Route.create({
                        'pol_id': other_port.id,
                        'pod_id': port.id,
                        'is_active': True,
                    })
                    
                    # Create product template for this route
                    self._create_product_template(route_pod_to_pol)
                    
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