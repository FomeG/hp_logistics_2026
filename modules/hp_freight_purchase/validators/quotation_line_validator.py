from .freight_validator import FreightValidator

class QuotationLineValidator(FreightValidator):
    """Handles different field names for same concepts"""
    @classmethod
    def validate_booking_line_form(cls, data, env):
        field_rules = {
            'quotation_line_container_type_id': {
                'label': f"Container Type",
                'field_name': 'container_type_id',
                'type': int,
                'exists': 'container.type',
                'required': True
            },
            'quotation_line_cost': {
                'label': f"Booking price",
                'field_name': 'cost',
                'type': (int, float),
                'min_value': 0,
                'required': True
            },
            'quotation_line_price': {
                'label': f"Internal Price",
                'field_name': 'price',
                'type': (int, float),
                'min_value': 0,
                'required': True
            },
        }

        errors = []
        validated = cls._validate(field_rules,data,env,errors)
        return (validated, errors) if not errors else ({}, errors)
