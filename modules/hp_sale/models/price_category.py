from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PriceCategory(models.Model):
    _name = 'product.price.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Price Category'
    _order = 'valid_until desc, id desc'

    product_id = fields.Many2one(
        'product.template', string='Product', required=True,
        domain="[('type', 'in', ['common', 'custom'])]"
    )

    price_type = fields.Selection([
        ('common', 'Common Price'),
        ('tiered', 'Tiered Pricing'),
    ], string='Price Type', required=True, readonly=True)

    # Price fields
    common_price = fields.Float(string='Giá chung', digits='Product Price', required=True)
    tiered_price = fields.Float(string='Giá lũy tiến', digits='Product Price')

    # Future prices
    future_common_price = fields.Float(string='Giá chung Tương lai', digits='Product Price', required=True)
    future_tiered_price = fields.Float(string='Giá lũy tiến Tương lai', digits='Product Price')

    # Validity period
    valid_until = fields.Date(string='Hiệu lực đến', required=True)

    # Status tracking
    is_superseded = fields.Boolean(
        string='Đã hết hiệu lực',
        default=False
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set price_type based on selected product_id"""
        if self.product_id and self.product_id.price_type:
            self.price_type = self.product_id.price_type
        else:
            self.price_type = "tiered"

    @api.constrains('valid_until')
    def _check_validity_dates(self):
        for record in self:
            if record.valid_until < fields.Date.today():
                raise ValidationError(_("Valid Until date must be in the future."))

    @api.constrains('price_type', 'common_price', 'tiered_price', 'future_common_price', 'future_tiered_price')
    def _check_price_values(self):
        """Ensure prices are positive"""
        for record in self:
            if record.price_type == 'common':
                if record.common_price <= 0 or record.future_common_price <= 0:
                    raise ValidationError(_("Common and Future Common Price must be positive."))
            elif record.price_type == 'tiered':
                if record.common_price <= 0 or record.tiered_price <= 0 or record.future_common_price <= 0 or record.future_tiered_price <= 0:
                    raise ValidationError(_("All price fields must be positive for Tiered Pricing."))

    @api.model
    def create(self, vals):
        """Create a new price category, supersede old ones, and update product price"""
        product = self.env['product.template'].browse(vals['product_id'])

        # Ensure price_type follows product_id
        if product and product.price_type:
            vals['price_type'] = product.price_type
        else:
            vals['price_type'] = "tiered"

        if product.type not in ['common', 'custom']:
            raise ValidationError(_("Price categories can only be created for products of type 'Common' or 'Custom'."))

        record = super(PriceCategory, self).create(vals)

        existing_categories = self.search([
            ('product_id', '=', vals['product_id']),
            ('id', '!=', record.id),
            ('is_superseded', '=', False)
        ])
        if existing_categories:
            existing_categories.write({'is_superseded': True})

        # Immediately update product price
        record._update_product_price()

        return record

    def write(self, vals):
        """Update product price when any price-related fields change"""
        result = super(PriceCategory, self).write(vals)
        price_fields = ['common_price', 'tiered_price', 'valid_until', 'future_common_price', 'future_tiered_price']
        if any(field in vals for field in price_fields):
            for record in self:
                record._update_product_price()
        return result

    def _update_product_price(self):
        self.ensure_one()
        today = fields.Date.today()

        # Apply prices only if this category is not superseded
        if not self.is_superseded and self.valid_until >= today:
            product = self.product_id

            if self.price_type == 'common':
                product.list_price = self.common_price
                product.tiered_price = None
            else:
                product.list_price = self.common_price
                product.tiered_price = self.tiered_price

            _logger.info(f"Updated prices for product {product.name} from price category {self.id}")

    @api.model
    def _cron_apply_future_prices(self):
        """Cron job to apply future prices when valid_until is reached"""
        today = fields.Date.today()

        # Find all price categories that expired today
        expired_categories = self.search([
            ('valid_until', '=', today),
            ('is_superseded', '=', False)
        ])
        for category in expired_categories:
            product = category.product_id
            if category.price_type == 'common':
                product.list_price = category.future_common_price
            else:
                product.list_price = category.future_common_price
                product.tiered_price = category.future_tiered_price

            _logger.info(f"Áp dụng giá tương lai cho sản phẩm {product.name} on {today}")

        return True
