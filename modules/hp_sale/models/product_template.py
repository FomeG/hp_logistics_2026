from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Add new product types while removing Odoo's default types
    def _selection_type(self):
        """ Remove Odoo's default types and only keep the custom ones. """
        return [
            ('pricing', "Pricing"),
            ('trucking', "Trucking"),
            ('common', "Common"),
            ('custom', "Custom"),
        ]

    type = fields.Selection(selection=_selection_type, required=True, default='pricing')
    
    complete_time = fields.Float(
        string="Thời gian hoàn thành (s)",
        digits=(3, 1),
        help="Thời gian hoàn thành dịch vụ"
    )
    
    # Fields for pricing type
    pod_id = fields.Char(
        string="Port of Departure",
        help="Port where goods will be loaded"
    )
    pol_id = fields.Char(
        string="Port of Loading",
        help="Port where goods will be unloaded"
    )
    etd = fields.Date(
        string="Estimated Departure Date",
        help="Estimated date of departure"
    )
    
    # Fields for trucking type
    start_id = fields.Char(
        string="Start",
        help="Starting location for trucking service"
    )
    destination_id = fields.Char(
        string="Destination",
        help="Destination location for trucking service"
    )
    @api.onchange('type')
    def _onchange_type(self):
        """Filter categories based on allowed product types"""
        domain = {}

        # For pricing and trucking types, no categories should be available
        if self.type in ['pricing', 'trucking']:
            self.categ_id = False  # Clear category if present

            # Reset fields based on new type to ensure consistency
            if self.type == 'pricing':
                self.start_id = False
                self.destination_id = False
                self.etd = False
            elif self.type == 'trucking':
                self.pod_id = False
                self.pol_id = False
                self.etd = False

        elif self.type in ['common', 'custom']:
            # Reset fields
            self.pod_id = False
            self.pol_id = False
            self.start_id = False
            self.destination_id = False
            self.etd = False
    
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
    
    @api.constrains('type', 'pod_id', 'pol_id', 'start_id', 'destination_id')
    def _check_required_fields_by_type(self):
        """Ensure required fields are set based on product type"""
        for product in self:
            if product.type == 'pricing' and (not product.pod_id or not product.pol_id or not product.etd):
                raise ValidationError(_("For Pricing products, Port of Departure, Port of Loading, and ETD are required."))
            elif product.type == 'trucking' and (not product.start_id or not product.destination_id or not product.etd):
                raise ValidationError(_("For Trucking products, Start Position, Destination, and ETD are required."))
