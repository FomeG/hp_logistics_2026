from .freight_validator import FreightValidator

# Validate create
class BookingCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'code': {
                'label': f"Code",
                'type': str,
                'unique': 'freight.purchase.booking',
                'required': True,
            },
            'vessel_id': {
                'label': f"Vessel",
                'type': int,
                'exists': 'freight.purchase.vessel',
                'required': True,
            },
            'etd': {
                'label': f"ETD",
                'type': str,
                'required': True,
            },
            'status': {
                'label': f"Status",
                'type': str,
                'in': {'draft', 'pending', 'confirmed', 'fully_assigned', 'shipped', 'cancelled', 'expired'},
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    

# validate update
class BookingUpdateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env, current_id):
        field_rules = {
            'code': {
                'label': f"Code",
                'type': str,
                'unique': 'freight.purchase.booking',
                'current_id': current_id
            },
            'vessel_id': {
                'label': f"Vessel",
                'type': int,
                'exists': 'freight.purchase.vessel',
            },
            'etd': {
                'label': f"ETD",
                'type': str,
            },
            'status': {
                'label': f"Status",
                'type': str,
                'in': {'draft', 'pending', 'confirmed', 'fully_assigned', 'shipped', 'cancelled', 'expired'},
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)