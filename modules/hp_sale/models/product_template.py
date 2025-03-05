from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Just override the type field definition
    type = fields.Selection(
        selection=[
            ('pricing', "Pricing"),
            ('trucking', "Trucking"),
            ('common', "Common"),
            ('custom', "Custom"),
        ],
        string="Product Type",
        required=True,
        default='pricing',
    )
    
    complete_time = fields.Float(
        string="Thời gian hoàn thành",
        digits=(3, 1),
        help="Thời gian hoàn thành dịch vụ dự kiến"
    )
    
    # Fields for pricing type
    pod_id = fields.Many2one(
        'res.partner',  # Assuming you store ports as partners, adjust if needed
        string="Port of Departure",
        domain=[('is_port', '=', True)],  # Assuming you have a field to identify ports
        help="Port where goods will be loaded"
    )
    pol_id = fields.Many2one(
        'res.partner',  # Adjust as needed
        string="Port of Loading",
        domain=[('is_port', '=', True)],
        help="Port where goods will be unloaded"
    )
    etd = fields.Date(
        string="Estimated Departure Date",
        help="Estimated date of departure"
    )
    
    # Fields for trucking type
    start_id = fields.Many2one(
        'res.partner',  # Adjust model as needed
        string="Start Position",
        help="Starting location for trucking service"
    )
    destination_id = fields.Many2one(
        'res.partner',  # Adjust model as needed
        string="Destination",
        help="Destination location for trucking service"
    )
    
    @api.constrains('categ_id', 'type')
    def _check_category_type_compatibility(self):
        for product in self:
            if product.categ_id and product.categ_id.allowed_type_id:
                # Get the allowed type value for this category
                allowed_type = product.categ_id.allowed_type_id.value
                
                if product.type != allowed_type:
                    raise ValidationError(_(
                        "Product type '%s' is not allowed for category '%s'. "
                        "Allowed type is: %s"
                    ) % (
                        dict(self._fields['type'].selection).get(product.type),
                        product.categ_id.name,
                        dict(self._fields['type'].selection).get(allowed_type)
                    ))
    
    @api.onchange('type')
    def _onchange_type(self):
        """Filter categories based on allowed product types"""
        domain = {}
        
        # For pricing and trucking types, no categories should be available
        if self.type in ['pricing', 'trucking']:
            domain['categ_id'] = [('id', '=', False)]  # Empty domain - no categories available
            self.categ_id = False  # Clear category if present
            
            # Reset fields based on new type to ensure consistency
            if self.type == 'pricing':
                self.start_id = False
                self.destination_id = False
            elif self.type == 'trucking':
                self.pod_id = False
                self.pol_id = False
        
        # For common and custom types, only show categories that allow these types
        elif self.type in ['common', 'custom']:
            allowed_categories = self.env['product.category'].search([
                '|',
                ('allowed_type_id', '=', False),  # No restrictions
                ('allowed_type_id.value', '=', self.type)  # Explicitly allows this type
            ])
            domain['categ_id'] = [('id', 'in', allowed_categories.ids)]
            
            # Reset fields
            self.pod_id = False
            self.pol_id = False
            self.start_id = False
            self.destination_id = False
        
        return {'domain': domain}
    
    def _can_have_price_category(self):
        """Determine if this product can have price categories based on its type"""
        self.ensure_one()
        return self.type in ['common', 'custom']
    
    # Add field for tiered pricing
    tiered_price = fields.Float(
        string="Tiered Price",
        digits='Product Price',
        help="Price for additional tiers or quantities"
    )
    
    price_type = fields.Selection([
        ('common', 'Common Price'),
        ('tiered', 'Tiered Pricing'),
    ], string='Price Type', default='common',
        help="Common price uses the same price for all items. Tiered pricing applies different prices based on quantity.")
    
    # For tracking price history
    price_category_ids = fields.One2many(
        'product.price.category', 'product_id',
        string='Price Categories',
        help="Price categories defined for this product"
    )
    
    can_have_price_category = fields.Boolean(
        string='Can Have Price Category',
        compute='_compute_can_have_price_category',
        store=True,
        help="Indicates if this product can have price categories (only for Common and Custom types)"
    )
    
    @api.depends('type')
    def _compute_can_have_price_category(self):
        """Compute if product can have price categories based on its type"""
        for product in self:
            product.can_have_price_category = product.type in ['common', 'custom']
    
    active_price_category_id = fields.Many2one(
        'product.price.category',
        string='Active Price Category',
        compute='_compute_active_price_category',
        store=False,
        help="Currently active price category for this product"
    )
    
    @api.depends('price_category_ids')
    def _compute_active_price_category(self):
        today = fields.Date.today()
        for product in self:
            active_category = self.env['product.price.category'].search([
                ('product_id', '=', product.id),
                ('valid_from', '<=', today),
                ('valid_until', '>=', today),
                ('is_superseded', '=', False)
            ], limit=1, order='create_date DESC')
            
            product.active_price_category_id = active_category.id if active_category else False
    
    @api.constrains('type', 'pod_id', 'pol_id', 'start_id', 'destination_id')
    def _check_required_fields_by_type(self):
        """Ensure required fields are set based on product type"""
        for product in self:
            if product.type == 'pricing' and (not product.pod_id or not product.pol_id or not product.etd):
                raise ValidationError(_("For Pricing products, Port of Departure, Port of Loading, and ETD are required."))
            elif product.type == 'trucking' and (not product.start_id or not product.destination_id or not product.etd):
                raise ValidationError(_("For Trucking products, Start Position, Destination, and ETD are required."))
                
    @api.constrains('type', 'categ_id')
    def _check_category_restrictions(self):
        """Ensure categories are only set for common and custom products"""
        for product in self:
            # Pricing and Trucking products should not have categories
            if product.type in ['pricing', 'trucking'] and product.categ_id:
                raise ValidationError(_("Products of type '%s' should not have a category assigned.") % 
                                    dict(self._fields['type'].selection).get(product.type))
            
            # Common and Custom products must have categories
            if product.type in ['common', 'custom'] and not product.categ_id:
                raise ValidationError(_("Products of type '%s' must have a category assigned.") % 
                                    dict(self._fields['type'].selection).get(product.type))