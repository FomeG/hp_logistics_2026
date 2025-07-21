from odoo import fields
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class FreightPurchaseQuotationService:
    """Service to handle quotation creation and synchronization"""
    
    def __init__(self, env):
        self.env = env

    def auto_create_quotation_from_booking_fees(self, booking):
        """Auto-create quotation from booking fees (internal method)"""
        if not booking:
            return
        
        # Create quotation for bookings without quotation (even if no fees initially)
        if not (booking.booking_mode == 'without_quotation' and not booking.quotation_id):
            return
        
        # Create quotation with same route and shipping line as booking
        quotation_vals = {
            'route_id': booking.route_id.id,
            'shipping_line_id': booking.shipping_line_id.id,
            'available_from': fields.Date.today(),
            'available_to': booking.etd,
            'is_active': True,
        }
        
        quotation = self.env['freight.purchase.quotation'].create(quotation_vals)
        
        # Copy common fees from booking to quotation
        for booking_fee in booking.fee_ids:
            self.env['freight.purchase.quotation.fee'].create({
                'quotation_id': quotation.id,
                'fee_type_id': booking_fee.fee_type_id.id,
                'amount': booking_fee.amount,
                'note': booking_fee.note,
            })
        
        # Create quotation lines for each booking line and copy fees
        for booking_line in booking.line_ids:
            if booking_line.container_type_id:
                # Create quotation line
                quotation_line_vals = {
                    'quotation_id': quotation.id,
                    'container_type_id': booking_line.container_type_id.id,
                    'cost': booking_line.unit_price,
                    'price': booking_line.unit_price,
                }
                
                quotation_line = self.env['freight.purchase.quotation.line'].create(quotation_line_vals)
                
                # Copy fees from booking line to quotation line
                for booking_line_fee in booking_line.fee_line_ids:
                    self.env['freight.purchase.quotation.line.fee'].create({
                        'quotation_line_id': quotation_line.id,
                        'fee_line_id': booking_line_fee.fee_line_id.id,
                        'amount': booking_line_fee.amount,
                    })
                
                # Update booking line to reference the new quotation line
                booking_line.quotation_line_id = quotation_line.id
        
        # Update booking to reference the new quotation
        booking.quotation_id = quotation.id
        
        _logger.info(f"Auto-created quotation {quotation.name} from booking {booking.name} fees")
        return quotation

    def sync_booking_fee_to_quotation(self, booking_fee):
        """Sync a booking fee to its quotation (bidirectional sync)"""
        if not booking_fee or not booking_fee.booking_id.quotation_id:
            return
        
        # Check if quotation fee already exists
        existing_quotation_fee = self.env['freight.purchase.quotation.fee'].search([
            ('quotation_id', '=', booking_fee.booking_id.quotation_id.id),
            ('fee_type_id', '=', booking_fee.fee_type_id.id),
        ], limit=1)
        
        if existing_quotation_fee:
            # Update existing
            existing_quotation_fee.write({
                'amount': booking_fee.amount,
                'note': booking_fee.note,
            })
            _logger.info(f"Updated quotation fee {existing_quotation_fee.id} from booking fee {booking_fee.id}")
        else:
            # Create new
            self.env['freight.purchase.quotation.fee'].create({
                'quotation_id': booking_fee.booking_id.quotation_id.id,
                'fee_type_id': booking_fee.fee_type_id.id,
                'amount': booking_fee.amount,
                'note': booking_fee.note,
            })
            _logger.info(f"Created quotation fee from booking fee {booking_fee.id}")

    def sync_booking_line_fee_to_quotation(self, booking_line_fee):
        """Sync a booking line fee to its quotation line (bidirectional sync)"""
        if not booking_line_fee or not booking_line_fee.booking_line_id.quotation_line_id:
            return
        
        # Check if quotation line fee already exists
        existing_quotation_line_fee = self.env['freight.purchase.quotation.line.fee'].search([
            ('quotation_line_id', '=', booking_line_fee.booking_line_id.quotation_line_id.id),
            ('fee_line_id', '=', booking_line_fee.fee_line_id.id),
        ], limit=1)
        
        if existing_quotation_line_fee:
            # Update existing
            existing_quotation_line_fee.write({
                'amount': booking_line_fee.amount,
            })
            _logger.info(f"Updated quotation line fee {existing_quotation_line_fee.id} from booking line fee {booking_line_fee.id}")
        else:
            # Create new
            self.env['freight.purchase.quotation.line.fee'].create({
                'quotation_line_id': booking_line_fee.booking_line_id.quotation_line_id.id,
                'fee_line_id': booking_line_fee.fee_line_id.id,
                'amount': booking_line_fee.amount,
            })
            _logger.info(f"Created quotation line fee from booking line fee {booking_line_fee.id}")

    def auto_create_quotation_line_from_booking_line_fees(self, booking_line):
        """Auto-create quotation line from booking line fees (internal method)"""
        if not booking_line:
            return
        
        if not (booking_line.fee_line_ids and not booking_line.quotation_line_id and booking_line.booking_id.quotation_id):
            return
        
        # Create quotation line
        quotation_line_vals = {
            'quotation_id': booking_line.booking_id.quotation_id.id,
            'container_type_id': booking_line.container_type_id.id,
            'cost': booking_line.unit_price,
            'price': booking_line.unit_price,
        }
        
        quotation_line = self.env['freight.purchase.quotation.line'].create(quotation_line_vals)
        
        # Copy fees from booking line to quotation line
        for booking_line_fee in booking_line.fee_line_ids:
            self.env['freight.purchase.quotation.line.fee'].create({
                'quotation_line_id': quotation_line.id,
                'fee_line_id': booking_line_fee.fee_line_id.id,
                'amount': booking_line_fee.amount,
            })
        
        # Update booking line to reference the new quotation line
        booking_line.quotation_line_id = quotation_line.id
        
        _logger.info(f"Auto-created quotation line for booking line {booking_line.id} with container type {booking_line.container_type_id.name}")
        return quotation_line

    def apply_fees_from_quotation_to_booking(self, booking):
        """Apply fees from quotation to booking - copy/update fees from quotation"""
        if not booking:
            raise UserError("No booking provided.")
        
        if not booking.quotation_id:
            raise UserError("No quotation linked to this booking.")
        
        # Check if quotation has fees
        has_quotation_fees = (
            len(booking.quotation_id.fee_ids) > 0 or 
            any(len(line.fee_line_ids) > 0 for line in booking.quotation_id.line_ids)
        )
        
        if not has_quotation_fees:
            raise UserError("Cannot apply fees. Quotation has no fees.")
        
        # Check if booking has lines with container types
        has_booking_lines_with_containers = any(line.container_type_id for line in booking.line_ids)
        
        # Clear existing fees first (to update them)
        booking.fee_ids.unlink()
        for booking_line in booking.line_ids:
            booking_line.fee_line_ids.unlink()
        
        # Copy common fees from quotation to booking (always)
        common_fees_count = 0
        for quotation_fee in booking.quotation_id.fee_ids:
            self.env['freight.purchase.booking.fee'].create({
                'booking_id': booking.id,
                'fee_type_id': quotation_fee.fee_type_id.id,
                'amount': quotation_fee.amount,
                'note': quotation_fee.note,
            })
            common_fees_count += 1
        
        # Copy container-specific fees from quotation lines to booking lines (only if booking lines exist)
        container_fees_count = 0
        if has_booking_lines_with_containers:
            _logger.info(f"Processing {len(booking.line_ids)} booking lines for container fees...")
            for booking_line in booking.line_ids:
                if booking_line.container_type_id:
                    _logger.info(f"Processing booking line {booking_line.id} with container type {booking_line.container_type_id.name}")
                    # Find matching quotation lines by container type
                    matching_quotation_lines = booking.quotation_id.line_ids.filtered(
                        lambda line: line.container_type_id.id == booking_line.container_type_id.id
                    )
                    
                    _logger.info(f"Found {len(matching_quotation_lines)} matching quotation lines")
                    
                    for quotation_line in matching_quotation_lines:
                        _logger.info(f"Processing quotation line {quotation_line.id} with {len(quotation_line.fee_line_ids)} fees")
                        for quotation_line_fee in quotation_line.fee_line_ids:
                            _logger.info(f"Creating booking line fee from quotation line fee {quotation_line_fee.id}")
                            self.env['freight.purchase.booking.line.fee'].create({
                                'booking_line_id': booking_line.id,
                                'fee_line_id': quotation_line_fee.fee_line_id.id,
                                'amount': quotation_line_fee.amount,
                            })
                            container_fees_count += 1
                            _logger.info(f"Successfully created booking line fee #{container_fees_count}")
                else:
                    _logger.info(f"Booking line {booking_line.id} has no container type, skipping")
        else:
            _logger.info("No booking lines with containers found")
        
        # Prepare result message
        if has_booking_lines_with_containers:
            message = f'Successfully applied {common_fees_count} common fees and {container_fees_count} container-specific fees from quotation.'
            message_type = 'success'
        else:
            message = f'Successfully applied {common_fees_count} common fees from quotation. Note: No booking lines found, so only common fees were applied. Create booking lines to apply container-specific fees.'
            message_type = 'warning'
        
        _logger.info(f"Applied fees from quotation {booking.quotation_id.name} to booking {booking.name}: {common_fees_count} common, {container_fees_count} container fees")
        
        return {
            'message': message,
            'type': message_type,
            'common_fees_count': common_fees_count,
            'container_fees_count': container_fees_count
        } 