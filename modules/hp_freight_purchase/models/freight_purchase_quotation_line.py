from odoo import models, fields, api, exceptions
from ..validators.quotation_line_validator import QuotationLineValidator
from ..services.freight_purchase_quotation_service import FreightPurchaseQuotationService
import logging
_logger = logging.getLogger(__name__)
class FreightPurchaseQuotationLine(models.Model):
    _name = 'freight.purchase.quotation.line'
    _description = 'Purchase Quotation Line'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(
        string="Name",
        compute='_compute_name',
        store=False
    )
    quotation_id = fields.Many2one(
        comodel_name='freight.purchase.quotation',
        index=True,
        required=True,
        ondelete='cascade'
    )
    container_type_id = fields.Many2one(
        comodel_name='container.type',
        index=True,
        required=True
    )
    cost = fields.Float(
        string="Booking price",
        required=True
    )
    price = fields.Float(
        string="Internal price set by sale director",
        default=lambda self: self.cost if self.cost else 0.0
    )
    fee_line_ids = fields.One2many(
        comodel_name="freight.purchase.quotation.line.fee",
        inverse_name="quotation_line_id",
        string="Fee Lines"
    )
    quotation_used_container_type_ids = fields.Many2many(
        'container.type',
        compute='_compute_quotation_used_container_types',
        store=False
    )

    @api.depends('quotation_id', 'container_type_id')
    def _compute_name(self):
        for record in self:
            if record.quotation_id and record.container_type_id:
                record.name = f"Quotation: {record.quotation_id.name} for container type: {record.container_type_id.name}"
            else:
                record.name = ''

    @api.model
    def create_from_booking_line_form(self, booking_line_form):
        try:
            validated, errors = QuotationLineValidator.validate_booking_line_form(booking_line_form, self.env)
            # Check required fields
            booking_id = booking_line_form.get('booking_id')
            if not booking_id:
                errors.append(f"Booking is required")
            booking = self.env['freight.purchase.booking'].browse(booking_id)
            if not booking.exists():
                errors.append(f"Booking #{booking_id} doesn't exist.")

            # Handle bookings without quotation
            if not booking.quotation_id:
                if booking.booking_mode == 'without_quotation':
                    # Create quotation automatically for bookings without quotation
                    quotation_service = FreightPurchaseQuotationService(self.env)
                    quotation_service.auto_create_quotation_from_booking_fees(booking)
                    
                    if not booking.quotation_id:
                        errors.append("Failed to create quotation for booking without quotation")
                else:
                    errors.append("Booking must have a quotation to create quotation lines")

            if errors:
                raise exceptions.ValidationError("\n".join([f"• {e}" for e in errors]))

            # Create quotation line with only relevant fields
            quotation_line_vals = {
                'quotation_id': booking.quotation_id.id,
                'container_type_id': validated.get('container_type_id'),
                'cost': validated.get('cost'),
                'price': validated.get('price'),
            }

            return self.create(quotation_line_vals)
        except exceptions.ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            _logger.exception(f"System error creating quotation line {e}")
            raise exceptions.ValidationError(f"A system error occurred, Cannot create quotation line. Please contact support.")

    @api.onchange('cost')
    def _onchange_cost(self):
        for record in self:
            if record.cost:
                record.price = record.cost

    @api.onchange('container_type_id')
    def _onchange_container_type_id(self):
        for line in self:
            default_ct_id = self.env.context.get('default_container_type_id')
            if default_ct_id and line.container_type_id and line.container_type_id.id != default_ct_id:
                raise exceptions.ValidationError('You can only select the container type passed from the quotation context')
    
    @api.depends('quotation_id.line_ids.container_type_id')
    def _compute_quotation_used_container_types(self):
        for record in self:
            if record.quotation_id:
                # Lấy các container type đã sử dụng, trừ chính record hiện tại
                used_types = record.quotation_id.line_ids.filtered(
                    lambda x: x.id != record.id
                ).mapped('container_type_id')
                record.quotation_used_container_type_ids = used_types
            else:
                record.quotation_used_container_type_ids = False

    def _auto_create_product_selling_week(self):
        quotation = self.quotation_id
        if not quotation or not quotation.available_from or not quotation.available_to:
            return
        
        # selling.week
        SellingWeek = self.env['selling.week']; 
        selling_week = SellingWeek.search([('freight_purchase_quotation_id', '=', quotation.id)], limit=1)
        if not selling_week:
            selling_week = SellingWeek.create({
                'name': f"Selling Week From {quotation.available_from} - {quotation.available_to}",
                'start_date': quotation.available_from,
                'end_date': quotation.available_to,
                'freight_purchase_quotation_id': quotation.id,
                'is_active': False,
            })
        
        from_location = quotation.from_location_id
        to_location = quotation.to_location_id
        if not from_location or not to_location:
            return

        # create product.template
        Product = self.env['product.template']
        product_template = Product.search([
            ('from_location_id', '=', from_location.id),
            ('to_location_id', '=', to_location.id)
        ], limit=1)
        if not product_template:
            Product.with_context(create_from_route=True).create({
                'type': 'pricing',
                'from_location_id': from_location.id,
                'to_location_id': to_location.id,
                'name': f"{from_location.name} -> {to_location.name}",
                'categ_id': self.env.ref('product.product_category_all').id,
                'uom_id': self.env.ref('uom.product_uom_unit').id,
                'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                'project_id': False,
                'project_template_id': False,
                'region_id': to_location.region_id.id if to_location.region_id else False,
            })
        else:
            product_template.write({
                'region_id': to_location.region_id.id if to_location.region_id else False,
            })

        # create product.template.selling.week
        ProductSellingWeek = self.env['product.template.selling.week']
        product_selling_week = ProductSellingWeek.search([
            ('selling_week_id', '=', selling_week.id),
            ('product_template_id', '=', product_template.id),
        ], limit=1)
        if not product_selling_week:
            product_selling_week = ProductSellingWeek.create({
                'goods_info': ' ',
                'selling_week_id': selling_week.id,
                'product_template_id': product_template.id,
            })

        # create product.template.selling.week.line
        self.env['product.template.selling.week.line'].create({
            'product_template_selling_week_id': product_selling_week.id,
            'shipping_line_id': quotation.shipping_line_id.id,
            'container_type_id': self.container_type_id.id,
            'price': self.price,
        })

        return True