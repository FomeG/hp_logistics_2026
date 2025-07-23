from .freight_validator import FreightValidator
from datetime import date

class BookingFeeValidator(FreightValidator):
    """Validates freight purchase booking fee creation and updates"""
    
    @classmethod
    def validate(cls, data, env, mode='create', current_id=None):
        field_rules = {
            'booking_id': {
                'label': 'Booking',
                'type': int,
                'exists': 'freight.purchase.booking',
                'required': True,
            },
            'fee_type_id': {
                'label': 'Fee Type',
                'type': int,
                'exists': 'freight.purchase.fee.type',
                'required': True,
            },
            'amount': {
                'label': 'Amount',
                'type': (int, float),
                'min_value': 0,
                'required': True,
            },
            'note': {
                'label': 'Note',
                'type': str,
            },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors, mode, current_id)
        
        # Custom validation: Check if fee type is common
        if validated.get('fee_type_id'):
            fee_type = env['freight.purchase.fee.type'].browse(validated['fee_type_id'])
            if not fee_type.is_common:
                errors.append("Only common fee types can be added to booking fees")
        
        # Custom validation: Check for duplicate fee type within same booking
        if validated.get('booking_id') and validated.get('fee_type_id'):
            domain = [
                ('booking_id', '=', validated['booking_id']),
                ('fee_type_id', '=', validated['fee_type_id'])
            ]
            if mode == 'write' and current_id:
                domain.append(('id', '!=', current_id))
            
            existing = env['freight.purchase.booking.fee'].sudo().search(domain, limit=1)
            if existing:
                errors.append("Fee already exists for this fee type in the selected booking")
        
        # Custom validation: Check if booking has quotation and validate fee availability
        if validated.get('booking_id'):
            booking = env['freight.purchase.booking'].browse(validated['booking_id'])
            if booking.quotation_id and validated.get('fee_type_id'):
                # Check if fee is available for the quotation's shipping line and direction
                fee_type = env['freight.purchase.fee.type'].browse(validated['fee_type_id'])
                if not cls._is_fee_available_for_booking(booking, fee_type, env):
                    errors.append(f"Fee type '{fee_type.name}' is not available for this booking's shipping line and direction")
        
        return (validated, errors) if not errors else ({}, errors)
    
    @classmethod
    def _is_fee_available_for_booking(cls, booking, fee_type, env):
        """Check if fee is available for the booking's context"""
        if not booking.quotation_id:
            return True  # Allow if no quotation (will be validated when quotation is created)
        
        # Check if there are any available fees for this fee type, shipping line, and direction
        available_fees = env['freight.purchase.fee'].sudo().search([
            ('fee_type_id', '=', fee_type.id),
            ('shipping_line_id', '=', booking.quotation_id.shipping_line_id.id),
            '|',
            ('date_from', '<=', date.today()),
            ('date_from', '=', False),
            '|',
            ('date_to', '>=', date.today()),
            ('date_to', '=', False),
        ], limit=1)
        
        return bool(available_fees)

class BookingLineFeeValidator(FreightValidator):
    """Validates freight purchase booking line fee creation and updates"""
    
    @classmethod
    def validate(cls, data, env, mode='create', current_id=None):
        field_rules = {
            'booking_line_id': {
                'label': 'Booking Line',
                'type': int,
                'exists': 'freight.purchase.booking.line',
                'required': True,
            },
            'fee_line_id': {
                'label': 'Fee Line',
                'type': int,
                'exists': 'freight.purchase.fee.line',
                'required': True,
            },
            'amount': {
                'label': 'Amount',
                'type': (int, float),
                'min_value': 0,
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors, mode, current_id)
        
        # Custom validation: Check if fee line is available for the booking line's context
        if validated.get('booking_line_id') and validated.get('fee_line_id'):
            booking_line = env['freight.purchase.booking.line'].browse(validated['booking_line_id'])
            fee_line = env['freight.purchase.fee.line'].browse(validated['fee_line_id'])
            
            if not cls._is_fee_line_available_for_booking_line(booking_line, fee_line, env):
                errors.append(f"Fee line '{fee_line.name}' is not available for this booking line's context")
        
        # Custom validation: Check for duplicate fee line within same booking line
        if validated.get('booking_line_id') and validated.get('fee_line_id'):
            domain = [
                ('booking_line_id', '=', validated['booking_line_id']),
                ('fee_line_id', '=', validated['fee_line_id'])
            ]
            if mode == 'write' and current_id:
                domain.append(('id', '!=', current_id))
            
            existing = env['freight.purchase.booking.line.fee'].sudo().search(domain, limit=1)
            if existing:
                errors.append("Fee already exists for this fee line in the selected booking line")
        
        # Custom validation: Check if booking line has container type
        if validated.get('booking_line_id'):
            booking_line = env['freight.purchase.booking.line'].browse(validated['booking_line_id'])
            if not booking_line.container_type_id:
                errors.append("Booking line must have a container type to add container-specific fees")
        
        return (validated, errors) if not errors else ({}, errors)
    
    @classmethod
    def _is_fee_line_available_for_booking_line(cls, booking_line, fee_line, env):
        """Check if fee line is available for the booking line's context"""
        if not booking_line.booking_id.quotation_id:
            return True  # Allow if no quotation (will be validated when quotation is created)
        
        # Check if fee line matches the booking line's context
        quotation = booking_line.booking_id.quotation_id
        
        # Check shipping line match
        if fee_line.shipping_line_id.id != quotation.shipping_line_id.id:
            return False
        
        # Check container type match
        if fee_line.container_type_id.id != booking_line.container_type_id.id:
            return False
        
        # Check direction match
        if fee_line.fee_type_id.direction != quotation.direction:
            return False
        
        # Check date availability
        today = date.today()
        if fee_line.date_from and fee_line.date_from > today:
            return False
        if fee_line.date_to and fee_line.date_to < today:
            return False
        
        return True 