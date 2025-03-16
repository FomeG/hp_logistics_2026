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
    pod_id = fields.Many2one(
        'pricing.pod',string="Cảng dỡ hàng",
        tracking=True
    )
    pol_id = fields.Many2one(
        'pricing.pol',string="Cảng xếp hàng",
        tracking=True
    )
    etd = fields.Date(
        string="Ngày khởi hành",
        help="Ngày khởi hành"
    )
    vol = fields.Char(string='Khối lượng vận chuyển', tracking=True)

    booking_id = fields.Many2one(
        'pricing.booking', string="Booking",
        tracking=True
    )
    
    # Fields for trucking type
    start_id = fields.Char(
        string="Điểm đi",
        help="Điểm xuất phát dịch vụ trucking"
    )
    destination_id = fields.Char(
        string="Điểm đến",
        help="Điểm đến dịch vụ trucking"
    )
    @api.onchange('type')
    def _onchange_type(self):
        """Filter categories based on allowed product types"""
        domain = {}

        # For pricing and trucking types, no categories should be available
        if self.type in ['pricing', 'trucking']:
            default_category = self.env.ref('product.product_category_all', raise_if_not_found=False)
            self.categ_id = default_category  # Clear category if present

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

    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        if self.booking_id:
            self.pod_id = self.booking_id.voyage_id.pod_id
            self.pol_id = self.booking_id.voyage_id.pol_id
            self.etd = self.booking_id.voyage_id.etd
            self.vol = self.booking_id.volume
            self.standard_price = self.booking_id.booking_price
    
    # Add field for tiered pricing
    tiered_price = fields.Float(
        string="Giá lũy tiến",
        digits='Product Price',
        help="Giá từ sp thứ 2"
    )
    
    price_type = fields.Selection([
        ('common', 'Common Price'),
        ('tiered', 'Tiered Pricing'),
    ], string='Price Type', default='common')
    
    @api.constrains('type', 'pod_id', 'pol_id', 'start_id', 'destination_id')
    def _check_required_fields_by_type(self):
        """Ensure required fields are set based on product type"""
        for product in self:
            if product.type == 'pricing' and (not product.pod_id or not product.pol_id or not product.etd):
                raise ValidationError(_("Với dịch vụ Pricing products, nội dung POL, POD, ETD là bắt buộc."))
            elif product.type == 'trucking' and (not product.start_id or not product.destination_id or not product.etd):
                raise ValidationError(_("Với dịch vụ Trucking, nội dung Điểm đi, Điểm đến, ETD là bắt buộc."))
