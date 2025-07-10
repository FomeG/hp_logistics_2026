from pkg_resources import require

from odoo import models, fields,api
from odoo.exceptions import ValidationError
from ..validators.port_validator import PortCreateValidator, PortUpdateValidator
import logging

_logger = logging.getLogger(__name__)

class FreightPurchasePort(models.Model):
    _name = 'freight.purchase.port'
    _description = 'Port'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin','unique.normalized.name.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    is_local = fields.Boolean(
        string='Is Local Port',
        required=False,
        default=False,
        tracking=True
    )
    region_id = fields.Many2one(
        'freight.purchase.region',
        string='Region',
        required=True,
        tracking=True
    )
    is_active = fields.Boolean(
        string='Is Active',
        default=True,
        tracking=True
    )
    employees = fields.Char(
        string="Employees in Region",
        compute='_compute_region_employees',
        store=False
    )

    @api.constrains('region_id')
    def _check_region_required(self):
        for record in self:
            if not record.region_id:
                raise ValidationError("Region is required for the port.")

    @api.depends('region_id.employee_ids')
    def _compute_region_employees(self):
        for port in self:
            if port.region_id and port.region_id.employee_ids:
                port.employees = ", ".join(port.region_id.employee_ids.mapped('name'))
            else:
                port.employees = ""
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = PortCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        
        records = super().create(vals_list)
        
        # Create routes and product templates for new ports (migrated from hp_pricing logic)
        for record in records:
            record._create_routes_and_products()
        
        return records
    
    def write(self, vals):
        for record in self:
            validated, errors = PortUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        
        result = super().write(vals)
        
        # Update routes and products when port name changes (migrated from hp_pricing logic)
        if 'name' in vals:
            for record in self:
                record._update_routes_and_products()
        
        return result

    def _create_routes_and_products(self):
        """
        Create routes and product templates for the new port with all existing ports.
        Migrated from hp_pricing POL/POD logic.
        """
        try:
            other_ports = self.env['freight.purchase.port'].search([
                ('id', '!=', self.id),
                ('is_active', '=', True)
            ])
            
            Route = self.env['freight.purchase.route']
            Product = self.env['product.template']
            
            for other_port in other_ports:
                # Create route from this port to other port (as POL -> POD)
                route_pol_to_pod = Route.search([
                    ('pol_id', '=', self.id),
                    ('pod_id', '=', other_port.id)
                ], limit=1)
                
                if not route_pol_to_pod:
                    route_pol_to_pod = Route.create({
                        'pol_id': self.id,
                        'pod_id': other_port.id,
                    })
                    
                    # Create product template for this route
                    self._create_product_template(route_pol_to_pod)
                
                # Create route from other port to this port (as POL -> POD)
                route_pod_to_pol = Route.search([
                    ('pol_id', '=', other_port.id),
                    ('pod_id', '=', self.id)
                ], limit=1)
                
                if not route_pod_to_pol:
                    route_pod_to_pol = Route.create({
                        'pol_id': other_port.id,
                        'pod_id': self.id,
                    })
                    
                    # Create product template for this route
                    self._create_product_template(route_pod_to_pol)
                    
        except Exception as e:
            _logger.exception(f"Error creating routes and products for port {self.name}: {e}")

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

    def _update_routes_and_products(self):
        """
        Update routes and related products when port name changes.
        """
        try:
            Route = self.env['freight.purchase.route']
            Product = self.env['product.template']
            
            # Find all routes that use this port (as POL or POD)
            routes_as_pol = Route.search([('pol_id', '=', self.id)])
            routes_as_pod = Route.search([('pod_id', '=', self.id)])
            
            all_routes = routes_as_pol + routes_as_pod
            
            for route in all_routes:
                # Update related products
                products = Product.search([('route_id', '=', route.id)])
                if products:
                    products.write({'name': route.name})
                    
        except Exception as e:
            _logger.exception(f"Error updating routes and products for port {self.name}: {e}")