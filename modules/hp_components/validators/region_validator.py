from .hp_validator import HpValidator

class RegionValidator(HpValidator):

    @classmethod
    def validate_create(cls, data, env):
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
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)

    @classmethod
    def validate_update(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Name",
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