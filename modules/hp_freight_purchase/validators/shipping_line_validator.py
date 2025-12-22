from .freight_validator import FreightValidator

# Validate create
class ShippingLineCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Shipping Line Name",
                'type': str,
                'required': True,
            },
            'email': {
                'label': f"Shipping Line Email",
                'type': str,
                'required': True,
                'format': 'email',
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    

# validate update
class ShippingLineUpdateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Shipping Line Name",
                'type': str,
                'required': False,
            },
            'email': {
                'label': f"Shipping Line Email",
                'type': str,
                'required': False,
                'format': 'email',
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)