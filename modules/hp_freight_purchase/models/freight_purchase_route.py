from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.route_validator import RouteCreateValidator, RouteUpdateValidator
import logging

_logger = logging.getLogger(__name__)

class FreightPurchaseRoute(models.Model):
    _name = 'freight.purchase.route'
    _description = 'Route'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Route Name',
        compute='_compute_route_name',
        store=True,
        index=True,
        tracking=True
    )
    pol_id = fields.Many2one(
        'freight.purchase.port',
        required=True,
        tracking=True
    )
    pod_id = fields.Many2one(
        'freight.purchase.port',
        required=True,
        tracking=True
    )
    direction = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('N/A', 'N/A'),
    ],
        required=True,
        compute='_compute_direction',
        default='export',
    )
    is_active = fields.Boolean(
        string='Is Active',
        default=True,
        tracking=True
    )
    quotation_ids = fields.One2many('freight.purchase.quotation', 'route_id', string='Quotations')

    total_quotations = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)

    @api.depends('pol_id.name', 'pod_id.name')
    def _compute_route_name(self):
        for route in self:
            if route.pod_id and route.pol_id:
                route.name = f"{route.pol_id.name} → {route.pod_id.name}"
            else:
                route.name = False
            

    # Constraints
    @api.constrains('pol_id', 'pod_id')
    def _check_ports(self):
        for route in self:
            if route.pol_id == route.pod_id:
                raise models.ValidationError("POL and POD cannot be the same!")
            
    @api.depends('quotation_ids')
    def _compute_total_quotation(self):
        for route in self:
            if route.quotation_ids:
                total = len(route.quotation_ids)
                route.total_quotations = f"{total} Quotation(s)"
            else:
                route.total_quotations = "0 Quotation(s)"

    @api.depends('pol_id.is_local', 'pod_id.is_local')
    def _compute_direction(self):
        for rec in self:
            rec.direction = False
            if rec.pod_id.is_local:
                rec.direction = 'import'
            elif rec.pol_id.is_local:
                rec.direction = 'export'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = RouteCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        
        records = super().create(vals_list)
        
        # Create product templates for new routes
        for record in records:
            record._create_product_template()
        
        return records
    
    def write(self, vals):
        for record in self:
            validated, errors = RouteUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        
        return super().write(vals)

    def _create_product_template(self):
        """
        Create a product template for this route when route is created manually.
        """
        try:
            Product = self.env['product.template']
            
            # Check if product already exists for this route
            existing_product = Product.search([
                ('route_id', '=', self.id),
                ('type', '=', 'pricing')
            ], limit=1)
            
            if not existing_product:
                Product.with_context(create_from_route=True).create({
                    'type': 'pricing',
                    'route_id': self.id,
                    'name': self.name,
                    'categ_id': self.env.ref('product.product_category_all').id,
                    'uom_id': self.env.ref('uom.product_uom_unit').id,
                    'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                    'project_id': False,
                    'project_template_id': False,
                })
                
        except Exception as e:
            _logger.exception(f"Error creating product template for route {self.name}: {e}")


