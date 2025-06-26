from odoo.tools import float_compare
import logging
import re
_logger = logging.getLogger(__name__)

class FreightValidator:

    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

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
                model_name = rules['exists']
                domain = [('id', '=', int(value))]
                if 'domain' in rules:
                    domain += rules['domain']
                if not env[model_name].sudo().search(domain, limit=1).exists():
                    errors.append(f"Selected {rules['label']} doesn't exist")
            
            if rules.get('format') == 'email' and value:
                if not cls.EMAIL_REGEX.match(value):
                    errors.append(f"{rules['label']} must be a valid email address")

            if rules.get('in') and value:
                if value not in rules['in']:
                    errors.append(f"{rules['label']} must be one of: {', '.join(rules['in'])}")

            if rules.get('unique') and value:
                model_name = rules['unique']
                domain = [(field_name, '=', value)]
                current_id = rules['current_id'] if 'current_id' in rules else False
                if current_id:
                    domain.append(('id', '!=', current_id))
                if env[model_name].sudo().search(domain, limit=1).exists():
                    errors.append(f"Booking code '{value}' already exists.")

            if value is not None:
                if rules.get('field_name'):
                    validated[rules.get('field_name')] = value
                else:
                    validated[field_name] = value

        return validated