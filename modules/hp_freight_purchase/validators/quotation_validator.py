from .freight_validator import FreightValidator

# Validate create
class QuotationCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'route_id': {
                'label': f"Route",
                'type': int,
                'exists': 'freight.purchase.route',
                'required': True,
            },
            'shipping_line_id': {
                'label': f"Shipping Line",
                'type': int,
                'exists': 'res.partner',
                'domain': [('is_shipping_line', '=', True)],
                'required': True,
            },
            'available_from': {
                'label': f"Available From",
                'type': str,
                'required': True,
            },
            'available_to': {
                'label': f"Available To",
                'type': str,
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
                'exists': 'freight.purchase.route',
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