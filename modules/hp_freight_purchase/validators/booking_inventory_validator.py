from .freight_validator import FreightValidator

# Validate create
class BookingInventoryValidator(FreightValidator):

    @classmethod
    def validate_create(cls, data, env):
        field_rules = {
            'booking_id': {
                'label': f"Booking",
                'type': int,
                'exists': 'freight.purchase.booking',
                'required': True,
            },
            'container_type_id': {
                'label': f"Container Type",
                'type': int,
                'exists': 'container.type',
                'required': True,
            },
            'quantity': {
                'label': f"Quantity",
                'type': int,
                'min_value': 1,
                'required': True
            },
            'action': {
                'label': f"Action",
                'type': str,
                'in': {'in', 'out', 'return'},
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    