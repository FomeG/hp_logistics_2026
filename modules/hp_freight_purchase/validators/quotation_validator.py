from .freight_validator import FreightValidator

# Validate create
class QuotationCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'route_id': {
                'label': f"Route",
                'type': int,
                'exists': 'route.base',
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
            'route_id': {
                'label': f"Route",
                'type': int,
                'exists': 'route.base',
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