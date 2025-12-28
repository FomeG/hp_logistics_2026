from .hp_validator import HpValidator


class ShippingLineValidator(HpValidator):

    rules = {
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
            'unique': 'res.partner',
        },
    }
    @classmethod
    def validate_create(cls, data, env):
        field_rules = cls.rules.copy()
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    @classmethod
    def validate_update(cls, data, env, record):
        field_rules = cls.rules.copy()
        field_rules['email']['current_id'] = record.id
        errors = []
        validated = cls._validate(field_rules,data,env,errors,'write', record)
        return (validated, errors) if not errors else ({}, errors)