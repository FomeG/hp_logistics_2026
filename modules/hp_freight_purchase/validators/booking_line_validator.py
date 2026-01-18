from .freight_validator import FreightValidator

class BookingLineValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'quantity': {
                'label': f"Quantity",
                'type': int,
                'min_value': 1,
                'required': True
            },
            'unit_price': {
                'label': f"Unit Price",
                'type': (int, float),
                'min_value': 0,
                'required': True
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
