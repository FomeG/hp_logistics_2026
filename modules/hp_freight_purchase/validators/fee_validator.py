import datetime

from .freight_validator import FreightValidator

# ==================== FEE TYPE VALIDATORS ====================
class FeeValidator(FreightValidator):

    @classmethod
    def validate_fee_type(cls, data, env, mode = 'create', record=None):
        field_rules = {
            'name': {
                'label': f"Name",
                'type': str,
                'required': True,
            },
            'direction': {
                'label': f"Direction",
                'type': str,
                'in': {'import', 'export'},
                'depends':'is_common',
                'condition': False
            },
            'is_common': {
                'type': bool,
                'label': f'Is Common',
            },
            'amount': {
                'depends': 'is_common',
                'condition': True,
                'required': True,
                'label': f"Amount",
                'type': (int, float),
                'min_value': 1.0
            }
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors, mode, record)
        return (validated, errors) if not errors else ({}, errors)

    @classmethod
    def validate_fee(cls, data, env, mode = 'create', record=None):
        field_rules = {
            'shipping_line_id': {
                'label': 'Shipping Line',
                'type': int,
                'exists': 'res.partner',
                'domain': [('partner_main_type_id.code', '=', 'shipping_line')],
                'required': True,
            },
            'fee_type_id': {
                'label': 'Fee Type',
                'type': int,
                'exists': 'freight.purchase.fee.type',
                'required': True,
            },
            'date_from': {
                'label': 'Date From',
                'required': False,
                'date': {
                    'format': '%Y-%m-%d',
                    'compare': {
                        'field': 'date_to',
                        'operator': '<=',
                        'message': 'Date From Must be before or equal to Date To'
                    }
                }
            },
            'date_to': {
                'label': 'Date To',
                'required': False,
                'date': {
                    'format': '%Y-%m-%d'
                }
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors, mode, record)
        return (validated, errors) if not errors else ({}, errors)

# validate update
class FeeTypeCreateValidator(FreightValidator):
    """Validates freight purchase fee type creation"""
    
    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': 'Name',
                'type': str,
                'required': True,
            },
            'type': {
                'label': 'Type',
                'type': str,
                'in': {'l', 'd', 'l/d'},
                'required': True,
            },
            'active': {
                'label': 'Active',
                'type': bool,
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors)
        return (validated, errors) if not errors else ({}, errors)

class FeeTypeUpdateValidator(FreightValidator):
    """Validates freight purchase fee type updates"""
    
    @classmethod
    def validate(cls, data, env, current_id=None):
        field_rules = {
            'name': {
                'label': 'Name',
                'type': str,
            },
            'type': {
                'label': 'Type',
                'type': str,
                'in': {'l', 'd', 'l/d'},
            },
            'active': {
                'label': 'Active',
                'type': bool,
            },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors)
        return (validated, errors) if not errors else ({}, errors)

# ==================== FEE VALIDATORS ====================

class FeeCreateValidator(FreightValidator):
    """Validates freight purchase fee creation"""
    
    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'shipping_line_id': {
                'label': 'Shipping Line',
                'type': int,
                'exists': 'res.partner',
                'domain': [('partner_main_type_id.code', '=', 'shipping_line')],
                'required': True,
            },
            'fee_type_id': {
                'label': 'Fee Type',
                'type': int,
                'exists': 'freight.purchase.fee.type',
                'required': True,
            },
            'date_from': {
                'label': 'Date From',
                'type': str,
                'required': False,
            },
            'date_to': {
                'label': 'Date To',
                'type': str,
                'required': False,
            },
            # 'note': {
            #     'label': 'Note',
            #     'type': str,
            #     'required': False,
            # },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors)
        
        # Custom validation: date_to should be after date_from
        if validated.get('date_from') and validated.get('date_to'):
            try:
                from datetime import datetime
                date_from = datetime.strptime(validated['date_from'], '%Y-%m-%d').date()
                date_to = datetime.strptime(validated['date_to'], '%Y-%m-%d').date()
                if date_to <= date_from:
                    errors.append("Date To must be after Date From")
            except ValueError:
                errors.append("Invalid date format. Use YYYY-MM-DD format")
        
        return (validated, errors) if not errors else ({}, errors)

class FeeUpdateValidator(FreightValidator):
    """Validates freight purchase fee updates"""
    
    @classmethod
    def validate(cls, data, env, current_id=None):
        field_rules = {
            'shipping_line_id': {
                'label': 'Shipping Line',
                'type': int,
                'exists': 'res.partner',
                'domain': [('partner_main_type_id.code', '=', 'shipping_line')],
            },
            'fee_type_id': {
                'label': 'Fee Type',
                'type': int,
                'exists': 'freight.purchase.fee.type',
            },
            'date_from': {
                'label': 'Date From',
                'type': str,
            },
            'date_to': {
                'label': 'Date To',
                'type': str,
            },
            'note': {
                'label': 'Note',
                'type': str,
            },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors)
        
        # Custom validation: date_to should be after date_from
        if validated.get('date_from') and validated.get('date_to'):
            try:
                from datetime import datetime
                date_from = datetime.strptime(validated['date_from'], '%Y-%m-%d').date()
                date_to = datetime.strptime(validated['date_to'], '%Y-%m-%d').date()
                if date_to <= date_from:
                    errors.append("Date To must be after Date From")
            except ValueError:
                errors.append("Invalid date format. Use YYYY-MM-DD format")
        
        return (validated, errors) if not errors else ({}, errors)

# ==================== FEE LINE VALIDATORS ====================

class FeeLineCreateValidator(FreightValidator):
    """Validates freight purchase fee line creation"""
    
    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'fee_id': {
                'label': 'Fee',
                'type': int,
                'exists': 'freight.purchase.fee',
                'required': True,
            },
            'container_type_id': {
                'label': 'Container Type',
                'type': int,
                'exists': 'container.type',
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
        validated = cls._validate(field_rules, data, env, errors)
        
        # Custom validation: Check for duplicate container type within same fee
        if validated.get('fee_id') and validated.get('container_type_id'):
            existing = env['freight.purchase.fee.line'].sudo().search([
                ('fee_id', '=', validated['fee_id']),
                ('container_type_id', '=', validated['container_type_id'])
            ], limit=1)
            if existing:
                errors.append("Fee line already exists for this container type in the selected fee")
        
        return (validated, errors) if not errors else ({}, errors)

class FeeLineUpdateValidator(FreightValidator):
    """Validates freight purchase fee line updates"""
    
    @classmethod
    def validate(cls, data, env, current_id=None):
        field_rules = {
            'fee_id': {
                'label': 'Fee',
                'type': int,
                'exists': 'freight.purchase.fee',
            },
            'container_type_id': {
                'label': 'Container Type',
                'type': int,
                'exists': 'container.type',
            },
            'amount': {
                'label': 'Amount',
                'type': (int, float),
                'min_value': 0,
            },
        }
        errors = []
        validated = cls._validate(field_rules, data, env, errors)
        
        # Custom validation: Check for duplicate container type within same fee (excluding current record)
        if validated.get('fee_id') and validated.get('container_type_id'):
            domain = [
                ('fee_id', '=', validated['fee_id']),
                ('container_type_id', '=', validated['container_type_id'])
            ]
            if current_id:
                domain.append(('id', '!=', current_id))
            
            existing = env['freight.purchase.fee.line'].sudo().search(domain, limit=1)
            if existing:
                errors.append("Fee line already exists for this container type in the selected fee")
        
        return (validated, errors) if not errors else ({}, errors)