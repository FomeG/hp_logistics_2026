from .freight_validator import FreightValidator
from datetime import date

class QuotationFeeValidator(FreightValidator):
    """Validates freight purchase quotation fee creation and updates"""
    
    @classmethod
    def validate(cls, data, env, mode='create', record=None):
        field_rules = {
            'quotation_id': {
                'label': 'Quotation',
                'type': int,
                'exists': 'freight.purchase.quotation',
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
            # 'note': {
            #     'label': 'Note',
            #     'type': str,
            # },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors, mode, record)
        
        # Custom validation: Check if fee type is common
        if validated.get('fee_type_id'):
            fee_type = env['freight.purchase.fee.type'].browse(validated['fee_type_id'])
            if not fee_type.is_common:
                errors.append("Only common fee types can be added to quotation fees")
        
        # Custom validation: Check for duplicate fee type within same quotation
        if validated.get('quotation_id') and validated.get('fee_type_id'):
            domain = [
                ('quotation_id', '=', validated['quotation_id']),
                ('fee_type_id', '=', validated['fee_type_id'])
            ]
            if mode == 'write' and record:
                domain.append(('id', '!=', record.id))
            
            existing = env['freight.purchase.quotation.fee'].sudo().search(domain, limit=1)
            if existing:
                errors.append("Fee already exists for this fee type in the selected quotation")
        
        # Custom validation: Check if fee is available for the quotation's context
        if validated.get('quotation_id') and validated.get('fee_type_id'):
            quotation = env['freight.purchase.quotation'].browse(validated['quotation_id'])
            fee_type = env['freight.purchase.fee.type'].browse(validated['fee_type_id'])
            if not cls._is_fee_available_for_quotation(quotation, fee_type, env):
                errors.append(f"Fee type '{fee_type.name}' is not available for this quotation's shipping line and direction")
        
        return (validated, errors) if not errors else ({}, errors)
    
    @classmethod
    def _is_fee_available_for_quotation(cls, quotation, fee_type, env):
        """Check if fee is available for the quotation's context"""
        # For common fee types, they are always available regardless of existing fee records
        if fee_type.is_common:
            return True
            
        # For non-common fee types, check if there are any available fees for this fee type, shipping line, and direction
        available_fees = env['freight.purchase.fee'].sudo().search([
            ('fee_type_id', '=', fee_type.id),
            ('shipping_line_id', '=', quotation.shipping_line_id.id),
            '|',
            ('date_from', '<=', date.today()),
            ('date_from', '=', False),
            '|',
            ('date_to', '>=', date.today()),
            ('date_to', '=', False),
        ], limit=1)
        
        return bool(available_fees)

class QuotationLineFeeValidator(FreightValidator):
    """Validates freight purchase quotation line fee creation and updates"""
    
    @classmethod
    def validate(cls, data, env, mode='create', record=None):
        field_rules = {
            'quotation_line_id': {
                'label': 'Quotation Line',
                'type': int,
                'exists': 'freight.purchase.quotation.line',
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
        validated = cls._validate(field_rules, data, env, errors, mode, record)
        
        # Custom validation: Check if fee line is available for the quotation line's context
        if validated.get('quotation_line_id') and validated.get('fee_line_id'):
            quotation_line = env['freight.purchase.quotation.line'].browse(validated['quotation_line_id'])
            fee_line = env['freight.purchase.fee.line'].browse(validated['fee_line_id'])
            
            if not cls._is_fee_line_available_for_quotation_line(quotation_line, fee_line, env):
                errors.append(f"Fee line '{fee_line.name}' is not available for this quotation line's context")
        
        # Custom validation: Check for duplicate fee line within same quotation line
        if validated.get('quotation_line_id') and validated.get('fee_line_id'):
            domain = [
                ('quotation_line_id', '=', validated['quotation_line_id']),
                ('fee_line_id', '=', validated['fee_line_id'])
            ]
            if mode == 'write' and record:
                domain.append(('id', '!=', record.id))
            
            existing = env['freight.purchase.quotation.line.fee'].sudo().search(domain, limit=1)
            if existing:
                errors.append("Fee already exists for this fee line in the selected quotation line")
        
        return (validated, errors) if not errors else ({}, errors)
    
    @classmethod
    def _is_fee_line_available_for_quotation_line(cls, quotation_line, fee_line, env):
        """Check if fee line is available for the quotation line's context"""
        quotation = quotation_line.quotation_id
        
        # Check shipping line match
        if fee_line.shipping_line_id.id != quotation.shipping_line_id.id:
            return False
        
        # Check container type match
        if fee_line.container_type_id.id != quotation_line.container_type_id.id:
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