from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)

class FreightPurchaseRouteListener(Component):
    _name = 'freight.purchase.route.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['route.base']

    def on_record_create(self, record, fields=None):
        """Handle route creation - create product template"""
        self._create_product_template(record)

    def _create_product_template(self, route):
        """
        Create a product template for this route when route is created manually.
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