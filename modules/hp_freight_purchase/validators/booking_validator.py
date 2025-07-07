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
            'quotation_id': {
                'label': f"Quotation",
                'type': int,
                'exists': 'freight.purchase.quotation',
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
            'booking_mode': {
                'label': f"Is Active",
                'type': str,
                'in': {'with_quotation', 'without_quotation'},
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
            'quotation_id': {
                'label': f"Quotation",
                'type': int,
                'exists': 'freight.purchase.quotation',
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
            'booking_mode': {
                'label': f"Is Active",
                'type': str,
                'in': {'with_quotation', 'without_quotation'},
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)