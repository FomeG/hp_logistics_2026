from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class PriceCategory(models.Model):
    _name = 'product.price.category'
    _description = 'Product Price Category'
    _order = 'valid_until desc, id desc'
    
    name = fields.Char(string='Name', required=True, copy=False)
    product_id = fields.Many2one('product.template', string='Product', required=True, 
                                 domain="[('type', 'in', ['common', 'custom'])]")
    price_type = fields.Selection([
        ('common', 'Common Price'),
        ('tiered', 'Tiered Pricing'),
    ], string='Price Type', required=True, default='common')
    
    # Price fields
    common_price = fields.Float(string='Common Price', digits='Product Price')
    tiered_price = fields.Float(string='Tiered Price', digits='Product Price')
    
    # Validity period
    valid_from = fields.Date(string='Valid From', default=fields.Date.today, required=True)
    valid_until = fields.Date(string='Valid Until', required=True)
    
    # Simple status field - just tracking if superseded by newer category
    is_superseded = fields.Boolean(
        string='Superseded',
        default=False,
        help="Indicates if this price category has been superseded by a newer one"
    )
    
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company)
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Price Category name must be unique!'),
    ]
    
    @api.constrains('valid_from', 'valid_until')
    def _check_validity_dates(self):
        for record in self:
            if record.valid_from > record.valid_until:
                raise ValidationError(_("Valid From date must be earlier than Valid Until date"))
    
    @api.constrains('price_type', 'common_price', 'tiered_price')
    def _check_price_values(self):
        for record in self:
            if record.price_type == 'common' and record.common_price <= 0:
                raise ValidationError(_("Common Price must be positive"))
            if record.price_type == 'tiered' and (record.common_price <= 0 or record.tiered_price <= 0):
                raise ValidationError(_("Both Base Price and Tiered Price must be positive"))
    
    @api.model
    def create(self, vals):
        # If product_id is provided, verify it's of type 'common' or 'custom'
        if 'product_id' in vals:
            product = self.env['product.template'].browse(vals['product_id'])
            if product.type not in ['common', 'custom']:
                raise ValidationError(_("Price categories can only be created for products of type 'Common' or 'Custom'."))
                
        record = super(PriceCategory, self).create(vals)
        
        # Mark all existing price categories for this product as superseded
        if 'product_id' in vals:
            existing_categories = self.search([
                ('product_id', '=', vals['product_id']),
                ('id', '!=', record.id),
                ('is_superseded', '=', False)
            ])
            if existing_categories:
                existing_categories.write({'is_superseded': True})
                # Log the superseding action
                for category in existing_categories:
                    category.message_post(
                        body=_("This price category has been superseded by %s") % record.name,
                        subject=_("Superseded")
                    )
        
        # Update product price immediately if this is the current active price category
        record._update_product_price()
        return record
    
    def write(self, vals):
        result = super(PriceCategory, self).write(vals)
        # If any price fields were changed, update the product
        price_fields = ['common_price', 'tiered_price', 'valid_from', 'valid_until']
        if any(field in vals for field in price_fields):
            for record in self:
                record._update_product_price()
        return result
    
    def _update_product_price(self):
        """Update the product's price if this price category is active"""
        self.ensure_one()
        today = fields.Date.today()
        
        # Only non-superseded price categories can update product prices
        if not self.is_superseded and self.valid_from <= today and self.valid_until >= today:
            product = self.product_id
            if self.price_type == 'common':
                # Update product with common price
                product.list_price = self.common_price
                # Clear tiered price
                product.tiered_price = 0.0
                product.price_type = 'common'
            else:
                # Update product with tiered prices
                product.list_price = self.common_price  # Base price
                product.tiered_price = self.tiered_price
                product.price_type = 'tiered'
            
            _logger.info(f"Updated prices for product {product.name} from price category {self.name}")
    
    @api.model
    def _cron_update_prices(self):
        """Cron job to update product prices based on valid price categories"""
        today = fields.Date.today()
        
        # Find all active and non-superseded price categories for today
        active_categories = self.search([
            ('valid_from', '<=', today),
            ('valid_until', '>=', today),
            ('is_superseded', '=', False)
        ])
        
        # Apply the price updates directly
        for category in active_categories:
            category._update_product_price()
        
        # Log completion of the job
        _logger.info(f"Price update cron job completed: updated {len(active_categories)} products")