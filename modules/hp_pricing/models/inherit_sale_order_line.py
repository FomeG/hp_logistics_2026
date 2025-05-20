from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_type_filter = fields.Selection([
        ('pricing', "Pricing"),
        ('trucking', "Trucking"),
        ('common', "Common"),
        ('custom', "Custom"),
    ], string="Product Type", default='common')

    etd_sale = fields.Date(
        string="ETD Sale",
        help="Estimated Time of Departure for this Sale Order Line"
    )

    base_price = fields.Float(
        string="Base Price",
        default=0.0
    )

    booking_id = fields.Many2one(
        'pricing.booking', string="Booking",
        domain="[('voyage_id.etd', '>=', etd_sale)]",
        tracking=True
    )

    pricing_quotation_id = fields.Many2one(
        'pricing.quotation', string="Pricing Quotation",
        domain="[('valid_to', '>=', etd_sale), ('sealine_id', '=', 'produc_template_id.sealine_id.id')]",
        tracking=True
    )

    volume_cont = fields.Selection([
        ('20DC', '20DC'),
        ('20RF', '20RF'),
        ('20OT', '20OT'),
        ('20HC', '20HC'),
        ('40DC', '40DC'),
        ('40HC', '40HC'),
        ('40HQ', '40HQ'),
        ('40RF', '40RF'),
        ('40HCRF', '40HCRF'),
        ('40OT', '40OT'),
    ], string="Container Type")

    commission = fields.Float(
        string="Commission (%)",
        default=0.0,
    )

    @api.onchange('product_type_filter')
    def _onchange_product_type_filter(self):
        # Clear product when type filter changes
        if self.product_id and self.product_id.product_tmpl_id.type != self.product_type_filter:
            self.product_id = False
            self.product_template_id = False

        # Clear booking-related fields if not pricing
        if self.product_type_filter != 'pricing':
            self.etd_sale = False
            self.booking_id = False
            self.volume_cont = False
            self.base_price = 0.0

    @api.onchange('etd_sale', 'product_template_id')
    def _onchange_auto_set_pricing_quotation(self):
        for record in self:
            if record.etd_sale and record.product_template_id and record.product_template_id.sealine_id:
                matching_quotation = self.env['pricing.quotation'].search([
                    ('valid_to', '>=', record.etd_sale),
                    ('sealine_id', '=', record.product_template_id.sealine_id.id)
                ], limit=1)

                if matching_quotation:
                    record.pricing_quotation_id = matching_quotation
                    record._onchange_booking_or_quotation()
                else:
                    record.pricing_quotation_id = False  # clear if nothing found
            else:
                record.pricing_quotation_id = False  # clear if conditions not met

    @api.onchange('booking_id', 'pricing_quotation_id', 'volume_cont')
    def _onchange_booking_or_quotation(self):
        for record in self:
            # Ensure only one is selected
            if record.booking_id and record.pricing_quotation_id:
                record.booking_id = False
                record.pricing_quotation_id = False
                raise UserError(_("Please select either a Booking OR a Pricing Quotation, not both."))

            record.base_price = 0.0  # Reset

            # Booking selected
            if record.booking_id:
                # Auto-fill ETD
                if record.booking_id.voyage_id and record.booking_id.voyage_id.etd:
                    record.etd_sale = record.booking_id.voyage_id.etd

                # Check volume_total validity
                if not record.booking_id.volume_total:
                    raise UserError(_("Booking has no valid volume total (TEU)."))

                # Determine base price based on container type
                cont = record.volume_cont
                if not cont:
                    raise UserError(_("Container type is required when Booking is selected."))

                if cont in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    multiplier = 2
                elif cont in ['20DC', '20RF', '20OT', '20HC']:
                    multiplier = 1
                else:
                    raise UserError(_("Unrecognized container type: %s") % cont)

                record.base_price = (
                                            record.booking_id.company_booking_price * multiplier
                                    ) / record.booking_id.volume_total

                # Check remaining TEU before assignment
                self._check_booking_teu_availability(record.booking_id, cont, record.product_uom_qty)

            # Quotation selected
            elif record.pricing_quotation_id:
                cont = record.volume_cont
                if not cont:
                    raise UserError(_("Container type is required when Quotation is selected."))

                if cont in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    record.base_price = record.pricing_quotation_id.cont_40_price
                elif cont in ['20DC', '20RF', '20OT', '20HC']:
                    record.base_price = record.pricing_quotation_id.cont_20_price
                else:
                    raise UserError(_("Unrecognized container type: %s") % cont)

            else:
                # Clear base_price if no booking or pricing quotation
                record.base_price = 0.0

    def _check_booking_teu_availability(self, booking, container_type, quantity):
        """Check if there's enough TEU available in the booking"""
        if not booking or not container_type:
            return

        # Calculate TEU needed for this line
        if container_type in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
            teu_needed = quantity * 2
        elif container_type in ['20DC', '20RF', '20OT', '20HC']:
            teu_needed = quantity * 1
        else:
            return

        # Calculate current usage (excluding this line if it already exists)
        current_usage = 0.0
        for line in booking.sale_line_ids:
            if line.id != self.id and line.order_id.state == 'sale' and line.volume_cont:
                if line.volume_cont in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    current_usage += line.product_uom_qty * 2
                elif line.volume_cont in ['20DC', '20RF', '20OT', '20HC']:
                    current_usage += line.product_uom_qty * 1

        remaining_teu = booking.volume_total - current_usage

        if teu_needed > remaining_teu:
            raise UserError(_(
                "Not enough TEU available in booking %s.\n"
                "Requested: %s TEU\n"
                "Available: %s TEU\n"
                "Total booking capacity: %s TEU"
            ) % (booking.booking_no, teu_needed, remaining_teu, booking.volume_total))

    @api.constrains('booking_id', 'volume_cont', 'product_uom_qty', 'order_id')
    def _check_booking_capacity_constraint(self):
        """Constraint to ensure booking capacity is not exceeded"""
        for record in self:
            if record.booking_id and record.volume_cont and record.order_id.state == 'sale':
                self._check_booking_teu_availability(record.booking_id, record.volume_cont, record.product_uom_qty)

    def action_create_pricing_sealine(self):
        """Open wizard to collect POD/POL information"""
        return {
            'name': _('Create POD/POL Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'pod.pol.request.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
