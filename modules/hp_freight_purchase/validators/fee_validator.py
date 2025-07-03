from .freight_validator import FreightValidator

class FeeValidator(FreightValidator):

    @classmethod
    def validate_fee_type(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Name",
                'type': str,
                'required': True,
            },
            'type': {
                'label': f"Type",
                'type': str,
                'required': True,
            }
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    @classmethod
    def validate_fee(cls, data, env):
        field_rules = {

        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
# validate update
class FeeUpdateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'name': {
                'label': f"Name",
                'type': str,
            },
            'amount': {
                'label': f"Amount",
                'min_value': 1,
                'type': (int, float),
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)