from odoo import models, fields, _, api
from datetime import date
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    _order = 'create_date desc'

    booking_line_id = fields.Many2one('freight.purchase.booking.line')
    container_type_id = fields.Many2one('container.type', string='Container Type')
    freight_booking_id = fields.Many2one(
        'freight.purchase.booking',
        string='Freight Booking',
        domain="[('etd', '>', '{}')]".format(date.today()),
        tracking=True
    )

    freight_quotation_id = fields.Many2one(
        'freight.purchase.quotation',
        domain=lambda self: self._get_freight_quotation_domain_lambda(),
        string="Freight Quotation",
        tracking=True
    )

    etd_sale = fields.Date(string="ETD Sale", help="Estimated Time of Departure for this Sale Order Line")
    base_price = fields.Float(string="Base Price", default=0.0)
    commission = fields.Float(string="Commission (%)", default=0.0)
    active = fields.Boolean(string="Active", default=True, track_visibility='onchange')

    product_type_filter = fields.Selection([
        ('pricing', "Pricing"),
        ('trucking', "Trucking"),
        ('common', "Common"),
        ('custom', "Custom"),
    ], string="Product Type (Filter)", default='common')

    def unlink(self):
        for line in self:
            if line.order_id.state == 'pricing_leader_confirm':
                raise UserError("Cannot delete confirmed order lines. Please set them as inactive.")
        return super().unlink()

    def _get_freight_quotation_domain_lambda(self):
        """Calculate domain for freight_quotation_id field using lambda approach"""
        # If we're in a new record creation context or missing required data
        if not self or not hasattr(self, 'etd_sale') or not hasattr(self, 'product_template_id'):
            return [('id', '=', False)]

        # For each record, calculate available quotations
        if not self.ids:  # Empty recordset
            return [('id', '=', False)]

        # Get all valid quotation IDs for current context
        valid_quotation_ids = []

        for record in self:
            if record.etd_sale and record.product_template_id and hasattr(record.product_template_id, 'route_id') and record.product_template_id.route_id:
                # Find quotations that match the criteria
                quotations = self.env['freight.purchase.quotation'].search([
                    ('route_id', '=', record.product_template_id.route_id.id),
                    '|',
                    ('available_to', '>=', record.etd_sale)
                ])
                valid_quotation_ids.extend(quotations.ids)

        # Remove duplicates
        valid_quotation_ids = list(set(valid_quotation_ids))

        if valid_quotation_ids:
            return [('id', 'in', valid_quotation_ids)]
        else:
            return [('id', '=', False)]

    @api.onchange('product_type_filter')
    def _onchange_product_type_filter(self):
        # Clear product when type filter changes
        if self.product_id and hasattr(self.product_id, 'product_tmpl_id') and self.product_id.product_tmpl_id.type != self.product_type_filter:
            self.product_id = False
            self.product_template_id = False

        # Clear booking-related fields if not pricing
        if self.product_type_filter != 'pricing':
            self.etd_sale = False
            self.freight_booking_id = False
            self.container_type_id = False
            self.base_price = 0.0

    @api.onchange('etd_sale', 'product_template_id')
    def _onchange_auto_set_freight_quotation(self):
        for record in self:
            if record.etd_sale and record.product_template_id and hasattr(record.product_template_id, 'route_id') and record.product_template_id.route_id:
                matching_quotation = self.env['freight.purchase.quotation'].search([
                    ('available_to', '>=', record.etd_sale),
                    ('route_id', '=', record.product_template_id.route_id.id)
                ], limit=1)

                if matching_quotation:
                    record.freight_quotation_id = matching_quotation
                    record._onchange_booking_or_quotation()
                else:
                    record.freight_quotation_id = False  # clear if nothing found
            else:
                record.freight_quotation_id = False  # clear if conditions not met

    @api.onchange('freight_booking_id', 'freight_quotation_id', 'container_type_id')
    def _onchange_booking_or_quotation(self):
        for record in self:
            # Ensure only one is selected
            if record.freight_booking_id and record.freight_quotation_id:
                record.freight_booking_id = False
                record.freight_quotation_id = False
                raise UserError(_("Please select either a Booking OR a Freight Quotation, not both."))

            record.base_price = 0.0  # Reset

            # Booking selected
            if record.freight_booking_id:
                # Auto-fill ETD
                if hasattr(record.freight_booking_id, 'etd') and record.freight_booking_id.etd:
                    record.etd_sale = record.freight_booking_id.etd

                # Check teu_volume validity
                if not record.freight_booking_id.teu_volume:
                    raise UserError(_("Booking has no valid volume total (TEU)."))

                # Determine base price based on container type
                if not record.container_type_id:
                    raise UserError(_("Container type is required when Booking is selected."))

                # Find the booking line that matches the container type
                matching_booking_line = record.freight_booking_id.line_ids.filtered(
                    lambda line: line.container_type_id.id == record.container_type_id.id
                )
                
                if not matching_booking_line:
                    raise UserError(_("No booking line found for container type %s in the selected booking.") % record.container_type_id.name)
                
                # Calculate average unit price from all matching booking lines
                total_unit_price = sum(line.price for line in matching_booking_line)
                average_unit_price = total_unit_price / len(matching_booking_line)
                record.base_price = average_unit_price

                # Check remaining TEU before assignment
                self._check_booking_teu_availability(record.freight_booking_id, record.container_type_id, record.product_uom_qty)

            # Quotation selected
            elif record.freight_quotation_id:
                if not record.container_type_id:
                    raise UserError(_("Container type is required when Quotation is selected."))

                # Find the quotation line that matches the container type
                matching_line = record.freight_quotation_id.line_ids.filtered(
                    lambda line: line.container_type_id.id == record.container_type_id.id
                )
                
                if matching_line:
                    # Calculate average unit price from all matching quotation lines
                    total_unit_price = sum(line.price for line in matching_line)
                    average_unit_price = total_unit_price / len(matching_line)
                    record.base_price = average_unit_price
                else:
                    raise UserError(_("No price found for container type %s in the selected quotation.") % record.container_type_id.name)

            else:
                # Clear base_price if no booking or quotation
                record.base_price = 0.0

    def _check_booking_teu_availability(self, booking, container_type, quantity):
        """Check if there's enough TEU available in the booking"""
        if not booking or not container_type:
            return

        # Calculate TEU needed for this line based on container name pattern
        cont_name = container_type.name
        if cont_name in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
            teu_needed = quantity * 2
        elif cont_name in ['20DC', '20RF', '20OT', '20HC']:
            teu_needed = quantity * 1
        else:
            return

        # Calculate current usage (excluding this line if it already exists)
        current_usage = 0.0
        for line in booking.sale_line_ids:
            if line.id != self.id and line.order_id.state == 'sale' and line.container_type_id:
                line_cont_name = line.container_type_id.name
                if line_cont_name in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                    current_usage += line.product_uom_qty * 2
                elif line_cont_name in ['20DC', '20RF', '20OT', '20HC']:
                    current_usage += line.product_uom_qty * 1

        remaining_teu = booking.teu_volume - current_usage

        if teu_needed > remaining_teu:
            raise UserError(_(
                "Not enough TEU available in booking %s.\n"
                "Requested: %s TEU\n"
                "Available: %s TEU\n"
                "Total booking capacity: %s TEU"
            ) % (booking.booking_no, teu_needed, remaining_teu, booking.teu_volume))

    @api.constrains('freight_booking_id', 'container_type_id', 'product_uom_qty', 'order_id')
    def _check_booking_capacity_constraint(self):
        """Constraint to ensure booking capacity is not exceeded"""
        for record in self:
            if record.freight_booking_id and record.container_type_id and record.order_id.state == 'sale':
                self._check_booking_teu_availability(record.freight_booking_id, record.container_type_id, record.product_uom_qty)

    def action_select_this_line(self):
        booking_line_id = self.env.context.get('booking_line_id')
        if booking_line_id:
            self.write({'booking_line_id': booking_line_id})
        return {'type': 'ir.actions.act_window_close'}

    def action_create_route(self):
        """Open wizard to collect Port/Route information"""
        return {
            'name': _('Create Port/Route Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.port.route.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {
            #     'default_sale_order_id': self.order_id.id
            # }
        }