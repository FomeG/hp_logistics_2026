from .freight_validator import FreightValidator

# Validate create
class PortCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Name",
                'type': str,
                'required': True,
            },
            'is_local': {
                'label': f"Is Local Port",
                'type': bool,
                'required': False,
            },
            'is_active': {
                'label': f"Is Active",
                'type': bool,
                'required': False,
            },
            'region_id': {
                'label': f"Region",
                'type': int,
                'exists': 'region',
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    

# validate update
class PortUpdateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Name",
                'type': str,
            },
            'is_local': {
                'label': f"Is Local Port",
                'type': bool,
            },
            'is_active': {
                'label': f"Is Active",
                'type': bool,
            },
            'region_id': {
                'label': f"Region",
                'type': int,
                'exists': 'region',
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)