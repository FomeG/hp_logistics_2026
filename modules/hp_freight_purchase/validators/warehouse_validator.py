from .freight_validator import FreightValidator

# Validate create
class WarehouseCreateValidator(FreightValidator):

    @classmethod
    def validate(cls, data, env):
        field_rules = {
            'booking_id': {
                'label': f"Booking",
                'type': int,
                'exists': 'freight.purchase.booking',
                'required': True,
            },
            'container_type_id': {
                'label': f"Container Type Warehouse",
                'type': int,
                'exists': 'container.type',
                'required': True,
            },
            'quantity': {
                'label': f"Quantity Warehouse",
                'type': int,
                'min_value': 1,
                'required': True
            },
            'action': {
                'label': f"Action Warehouse",
                'type': str,
                'in': {'in', 'out', 'return'},
                'required': True,
            },
        }
        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
    