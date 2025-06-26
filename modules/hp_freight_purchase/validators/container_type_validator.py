from .freight_validator import FreightValidator

# Validate create
class ContainerTypeCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Name",
                'type': str,
                'required': True,
            },
            'is_active': {
                'label': f"Is Active",
                'type': bool,
                'required': True,
            },
            'teu': {
                'label': f"TEU",
                'type': (int, float),
                'min_value': 1,
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    

# validate update
class ContainerTypeUpdateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Name",
                'type': str,
            },
            'is_active': {
                'label': f"Is Active",
                'type': bool,
            },
            'teu': {
                'label': f"TEU",
                'min_value': 1,
                'type': (int, float),
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)