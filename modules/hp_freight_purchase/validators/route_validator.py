from .freight_validator import FreightValidator

# Validate create
class RouteCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'is_active': {
                'label': f"Is Active",
                'type': bool,
                'required': True,
            },
            'pol_id': {
                'label': f"POL",
                'type': int,
                'exists': 'location.base',
                'required': True,
            },
            'pod_id': {
                'label': f"POD",
                'type': int,
                'exists': 'location.base',
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    

# validate update
class RouteUpdateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'is_active': {
                'label': f"Is Active",
                'type': bool,
            },
            'pol_id': {
                'label': f"POL",
                'type': int,
                'exists': 'freight.purchase.port',
            },
            'pod_id': {
                'label': f"POD",
                'type': int,
                'exists': 'freight.purchase.port',
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)