from odoo.tools import float_compare
import logging
_logger = logging.getLogger(__name__)

class FreightValidator:

    @classmethod
    def _validate(cls, field_rules, data, env, errors):
        validated = {}

        for field_name, rules in field_rules.items():
            value = data.get(field_name)

            if rules.get('required') and value is None:
                errors.append(f"Missing required field: {rules['label']}")
                continue

            if value is not None and not isinstance(value, rules['type']):
                errors.append(f"{rules['label']} must be a {str(rules['type'])}")
                continue

            if rules.get('min_value') and isinstance(value, (int, float)):
                if float_compare(value, rules['min_value'], precision_digits=2) < 0:
                    errors.append(f"{rules['label']} must be ≥ {rules['min_value']}")

            if rules.get('exists') and value:
                if not env[rules['exists']].browse(int(value)).exists():
                    errors.append(f"Selected {rules['label']} doesn't exist")

            if value is not None:
                if rules.get('field_name'):
                    validated[rules.get('field_name')] = value
                else:
                    validated[field_name] = value

        return validated