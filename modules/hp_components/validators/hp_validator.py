import operator
from datetime import datetime, date

from odoo.tools import float_compare
import logging
import re
_logger = logging.getLogger(__name__)

class HpValidator:

    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    @classmethod
    def _validate_min(cls, errors, rules, value):
        if rules.get('min_value') is not None and isinstance(value, (int, float)):
            if float_compare(value, rules['min_value'], precision_digits=2) < 0:
                errors.append(f"{rules['label']} must be ≥ {rules['min_value']}")
                return False
        return True

    @classmethod
    def _to_date(cls,val):
        if isinstance(val, date):
            return val
        if isinstance(val, str):
            try:
                return datetime.strptime(val, "%Y-%m-%d").date()
            except ValueError:
                pass
        return None

    @classmethod
    def _validate_date_field(cls, value, field_rules, errors):
        if value is None or value == False or value == '':
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return datetime.strptime(value, field_rules['date']['format']).date()
            except ValueError:
                errors.append(f"Invalid date format for {field_rules['label']}. Use {field_rules['date']['format']}")
            except TypeError:
                errors.append(f"Invalid date value for {field_rules['label']}")
        else:
            errors.append(f"{field_rules['label']} must be string or date, got {type(value)}")
        return None

    @classmethod
    def _validate_date_comparisons(cls, validated, field_rules, errors, existing_values=None):
        existing_values = existing_values or {}
        ops = {
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            '==': operator.eq
        }
        effective_values = {**existing_values, **validated}
        for field_name, rules in field_rules.items():
            if 'date' in rules and 'compare' in rules['date']:
                cmp = rules['date']['compare']
                target_field = cmp['field']
                if field_name in effective_values and target_field in effective_values:
                    a = cls._to_date(effective_values[field_name])
                    b = cls._to_date(effective_values[target_field])
                    if not (isinstance(a, date) and isinstance(b, date)):
                        continue
                    if not ops[cmp['operator']](a, b):
                        errors.append(cmp['message'])
                        return False
        return True

    @classmethod
    def _validate(cls, field_rules, data, env, errors, mode='create', record=None):
        validated = {}
        input_fields = set(data.keys())
        # Get existing values for update case
        existing_values = {}
        if mode == 'write' and record:
            for field in field_rules.keys():
                if field in record._fields:
                    value = record._fields[field].convert_to_write(record[field], record)
                    if 'date' in field_rules[field] and value is False:
                        existing_values[field] = None
                    else:
                        existing_values[field] = value
                else:
                    existing_values[field] = None

        for field_name, rules in field_rules.items():

            value = data.get(field_name, existing_values.get(field_name) if mode == 'write' else None)

            if rules.get('depends'):
                main_field = rules['depends']
                if data.get(main_field) == rules['condition']:
                    if rules.get('required') and value is None:
                        errors.append(f"{rules['label']} is required when {main_field} is set")
                        continue
                    if not cls._validate_min(errors, rules, value):
                        continue
                    if rules.get('type') and value is not None and not isinstance(value, rules['type']):
                        errors.append(f"{rules['label']} must be a {str(rules['type'])}")
                        continue
                    if rules.get('in') and value:
                        if value not in rules['in']:
                            errors.append(f"{rules['label']} must be one of: {', '.join(rules['in'])}")
                            continue
                else:
                    continue

            if 'date' in rules:
                validated[field_name] = cls._validate_date_field(value, rules, errors)

            if rules.get('required') and value is None:
                errors.append(f"Missing required field: {rules['label']}")
                continue

            if rules.get('type') and value is not None and not isinstance(value, rules['type']):
                errors.append(f"{rules['label']} must be a {str(rules['type'])}")
                continue
            if not cls._validate_min(errors, rules, value):
                continue
            if rules.get('exists') and value:
                model_name = rules['exists']
                domain = [('id', '=', int(value))]
                if 'domain' in rules:
                    domain += rules['domain']
                if not env[model_name].sudo().search(domain, limit=1).exists():
                    errors.append(f"Selected {rules['label']} doesn't exist")
                    continue
            
            if rules.get('format') == 'email' and value:
                if not cls.EMAIL_REGEX.match(value):
                    errors.append(f"{rules['label']} must be a valid email address")
                    continue

            if rules.get('in') and value:
                if value not in rules['in']:
                    errors.append(f"{rules['label']} must be one of: {', '.join(rules['in'])}")
                    continue

            if rules.get('unique') and value:
                model_name = rules['unique']
                domain = [(field_name, '=', value)]
                current_id = rules['current_id'] if 'current_id' in rules else False
                if current_id:
                    domain.append(('id', '!=', current_id))
                if env[model_name].sudo().search(domain, limit=1).exists():
                    errors.append(f"'{value}' already exists.")
                    continue

            if value is not None:
                if rules.get('field_name'):
                    validated[rules.get('field_name')] = value
                else:
                    validated[field_name] = value

        if not cls._validate_date_comparisons(validated, field_rules, errors, existing_values if mode == 'write' else {}):
            return  validated

        rules_keys = set(field_rules.keys())
        if len(input_fields) != len(rules_keys):
            for key in input_fields.difference(rules_keys):
                if data.get(key):
                    validated[key] = data[key]
        return validated