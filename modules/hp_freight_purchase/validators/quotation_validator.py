from .freight_validator import FreightValidator

# Validate create
class QuotationCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'from_location_id': {
                'label': f"From",
                'type': int,
                'exists': 'location.base',
                'required': True,
            },
            'to_location_id': {
                'label': f"To",
                'type': int,
                'exists': 'location.base',
                'required': True,
            },
            'shipping_line_id': {
                'label': f"Shipping Line",
                'type': int,
                'exists': 'res.partner',
                'domain': [('partner_main_type_id.code', '=', 'shipping_line')],
                'required': True,
            },
            'available_from': {
                'label': f"Available From",
                'date': {
                    'format': '%Y-%m-%d'
                },
                'required': True,
            },
            'available_to': {
                'label': f"Available To",
                'date': {
                    'format': '%Y-%m-%d'
                },
                'required': True,
            },
            'is_active': {
                'label': f"Is Active",
                'type': bool,
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    

# validate update
class QuotationUpdateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'from_location_id': {
                'label': f"From",
                'type': int,
                'exists': 'location.base',
            },
            'to_location_id': {
                'label': f"To",
                'type': int,
                'exists': 'location.base',
            },
            'shipping_line_id': {
                'label': f"Shipping Line",
                'type': int,
                'exists': 'res.partner',
            },
            'available_from': {
                'label': f"Available From",
                'type': str,
            },
            'available_to': {
                'label': f"Available To",
                'type': str,
            },
            'is_active': {
                'label': f"Is Active",
                'type': bool,
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)