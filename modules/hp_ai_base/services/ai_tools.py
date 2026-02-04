# -*- coding: utf-8 -*-
"""
AI Tools - Provider-agnostic tool definitions and executor

This module defines tools that AI can call to interact with Odoo.
Tools are defined once and adapted for each provider (OpenAI, Anthropic, Gemini).
"""

import json
import logging
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# =============================================================================
# TOOL DEFINITIONS (Provider-agnostic)
# =============================================================================

ODOO_AI_TOOLS = [
    {
        "name": "get_field_value",
        "description": "Get the value of a specific field from the current record. Use this to retrieve any field data like dates, amounts, status, names, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "The field name to retrieve (e.g., 'name', 'state', 'amount_total', 'date_order')"
                }
            },
            "required": ["field_name"]
        }
    },
    {
        "name": "get_related_record",
        "description": "Get details of a Many2one related record (e.g., partner details, currency details, user details)",
        "parameters": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "The Many2one field name (e.g., 'partner_id', 'currency_id', 'user_id')"
                },
                "fields_to_read": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of fields to read from the related record. If empty, returns common fields."
                }
            },
            "required": ["field_name"]
        }
    },
    {
        "name": "get_line_items",
        "description": "Get One2many line items (e.g., order lines, invoice lines) with their details",
        "parameters": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "The One2many field name (e.g., 'order_line', 'invoice_line_ids', 'line_ids')"
                },
                "fields_to_read": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of fields to read from each line. If empty, returns common fields."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to return (default: 50)"
                }
            },
            "required": ["field_name"]
        }
    },
    {
        "name": "get_record_summary",
        "description": "Get a comprehensive summary of the current record including all important fields and related data",
        "parameters": {
            "type": "object",
            "properties": {
                "include_lines": {
                    "type": "boolean",
                    "description": "Whether to include line items in the summary (default: true)"
                }
            }
        }
    },
    {
        "name": "search_records",
        "description": "Search for records in any Odoo model. Use this to find related information not directly linked to the current record.",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "The Odoo model to search (e.g., 'res.partner', 'product.product', 'sale.order')"
                },
                "domain": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A domain tuple like ['field', 'operator', 'value']"
                    },
                    "description": "Odoo domain filter as list of tuples (e.g., [['is_company', '=', true], ['country_id.code', '=', 'VN']])"
                },
                "fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fields to return for each record"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default: 10)"
                }
            },
            "required": ["model"]
        }
    },
    {
        "name": "get_model_fields",
        "description": "Get available fields for the current model or a specified model. Use this to discover what data is available.",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "The model to get fields for. If empty, uses the current record's model."
                },
                "field_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by field types (e.g., ['many2one', 'one2many', 'char', 'float']). If empty, returns all types."
                }
            }
        }
    }
]


class AIToolExecutor(models.AbstractModel):
    """
    Executes AI tool calls against Odoo records.
    
    This is a stateless service that takes a record and executes tools on it.
    """
    _name = 'ai.tool.executor'
    _description = 'AI Tool Executor'

    # =========================================================================
    # MAIN EXECUTION METHOD
    # =========================================================================

    @api.model
    def execute_tool(self, tool_name, tool_args, record):
        """
        Execute a tool and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Dictionary of tool arguments
            record: The Odoo record to operate on
            
        Returns:
            dict with 'success' and 'result' or 'error'
        """
        try:
            method = getattr(self, f'_tool_{tool_name}', None)
            if not method:
                return {
                    'success': False,
                    'error': f"Unknown tool: {tool_name}"
                }
            
            result = method(record, tool_args)
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            _logger.exception(f"Tool execution error: {tool_name}")
            return {
                'success': False,
                'error': str(e)
            }

    # =========================================================================
    # TOOL IMPLEMENTATIONS
    # =========================================================================

    @api.model
    def _tool_get_field_value(self, record, args):
        """Get a single field value"""
        field_name = args.get('field_name')
        if not field_name:
            return {'error': 'field_name is required'}
        
        if not hasattr(record, field_name):
            return {'error': f"Field '{field_name}' does not exist on {record._name}"}
        
        value = getattr(record, field_name)
        return self._format_field_value(record, field_name, value)

    @api.model
    def _tool_get_related_record(self, record, args):
        """Get details of a Many2one related record"""
        field_name = args.get('field_name')
        fields_to_read = args.get('fields_to_read', [])
        
        if not field_name:
            return {'error': 'field_name is required'}
        
        if not hasattr(record, field_name):
            return {'error': f"Field '{field_name}' does not exist on {record._name}"}
        
        related = getattr(record, field_name)
        if not related:
            return {'value': None, 'message': f'{field_name} is not set'}
        
        # Auto-detect common fields if not specified
        if not fields_to_read:
            fields_to_read = self._get_common_fields(related)
        
        result = {'id': related.id}
        for fname in fields_to_read:
            if hasattr(related, fname):
                result[fname] = self._format_field_value(related, fname, getattr(related, fname))
        
        return result

    @api.model
    def _tool_get_line_items(self, record, args):
        """Get One2many line items"""
        field_name = args.get('field_name')
        fields_to_read = args.get('fields_to_read', [])
        limit = args.get('limit', 50)
        
        if not field_name:
            return {'error': 'field_name is required'}
        
        if not hasattr(record, field_name):
            return {'error': f"Field '{field_name}' does not exist on {record._name}"}
        
        lines = getattr(record, field_name)
        if not lines:
            return {'lines': [], 'count': 0}
        
        # Auto-detect common fields if not specified
        if not fields_to_read and lines:
            fields_to_read = self._get_common_fields(lines[0])
        
        result_lines = []
        for idx, line in enumerate(lines[:limit]):
            line_data = {'index': idx + 1}
            for fname in fields_to_read:
                if hasattr(line, fname):
                    line_data[fname] = self._format_field_value(line, fname, getattr(line, fname))
            result_lines.append(line_data)
        
        return {
            'lines': result_lines,
            'count': len(lines),
            'showing': min(limit, len(lines))
        }

    @api.model
    def _tool_get_record_summary(self, record, args):
        """Get comprehensive record summary"""
        include_lines = args.get('include_lines', True)
        
        summary = {
            'model': record._name,
            'id': record.id,
            'fields': {}
        }
        
        # Get all readable fields
        for field_name, field_obj in record._fields.items():
            if field_name.startswith('_') or field_name in ['id', 'create_uid', 'write_uid', 'create_date', 'write_date', '__last_update']:
                continue
            
            try:
                value = getattr(record, field_name)
                
                # Skip One2many/Many2many unless include_lines
                if field_obj.type == 'one2many':
                    if include_lines:
                        lines = getattr(record, field_name)
                        if lines:
                            summary['fields'][field_name] = {
                                'type': 'one2many',
                                'count': len(lines),
                                'items': self._tool_get_line_items(record, {'field_name': field_name, 'limit': 20})['lines']
                            }
                    continue
                elif field_obj.type == 'many2many':
                    if value:
                        summary['fields'][field_name] = {
                            'type': 'many2many',
                            'count': len(value),
                            'items': [{'id': r.id, 'name': getattr(r, 'name', str(r.id))} for r in value[:10]]
                        }
                    continue
                elif field_obj.type == 'binary':
                    # Skip binary fields
                    continue
                
                formatted = self._format_field_value(record, field_name, value)
                if formatted is not None and formatted != '' and formatted != False:
                    summary['fields'][field_name] = formatted
                    
            except Exception as e:
                _logger.debug(f"Could not read field {field_name}: {e}")
                continue
        
        return summary

    @api.model
    def _tool_search_records(self, record, args):
        """Search records in any model"""
        model_name = args.get('model')
        domain = args.get('domain', [])
        fields = args.get('fields', ['id', 'name', 'display_name'])
        limit = args.get('limit', 10)
        
        if not model_name:
            return {'error': 'model is required'}
        
        try:
            Model = self.env[model_name]
        except KeyError:
            return {'error': f"Model '{model_name}' does not exist"}
        
        # Security check - only allow reading
        records = Model.search(domain, limit=limit)
        
        result = []
        for rec in records:
            rec_data = {'id': rec.id}
            for fname in fields:
                if hasattr(rec, fname):
                    rec_data[fname] = self._format_field_value(rec, fname, getattr(rec, fname))
            result.append(rec_data)
        
        return {
            'model': model_name,
            'count': len(result),
            'records': result
        }

    @api.model
    def _tool_get_model_fields(self, record, args):
        """Get available fields for a model"""
        model_name = args.get('model') or record._name
        field_types = args.get('field_types', [])
        
        try:
            Model = self.env[model_name]
        except KeyError:
            return {'error': f"Model '{model_name}' does not exist"}
        
        fields_info = []
        for field_name, field_obj in Model._fields.items():
            if field_name.startswith('_'):
                continue
            if field_types and field_obj.type not in field_types:
                continue
            
            fields_info.append({
                'name': field_name,
                'type': field_obj.type,
                'string': field_obj.string,
                'required': field_obj.required,
                'readonly': field_obj.readonly,
            })
        
        return {
            'model': model_name,
            'fields': sorted(fields_info, key=lambda x: x['name'])
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @api.model
    def _format_field_value(self, record, field_name, value):
        """Format a field value for AI consumption"""
        if value is None or value is False:
            return None
        
        field_obj = record._fields.get(field_name)
        if not field_obj:
            return str(value)
        
        if field_obj.type == 'many2one':
            return {
                'id': value.id,
                'name': getattr(value, 'name', None) or getattr(value, 'display_name', str(value.id))
            } if value else None
        elif field_obj.type == 'selection':
            # Get selection label
            selection = field_obj.selection
            if callable(selection):
                selection = selection(record)
            label = dict(selection).get(value, value)
            return {'value': value, 'label': label}
        elif field_obj.type in ('date', 'datetime'):
            return str(value) if value else None
        elif field_obj.type == 'monetary':
            currency_field = field_obj.currency_field
            currency = getattr(record, currency_field, None) if currency_field else None
            return {
                'amount': value,
                'currency': currency.name if currency else 'USD'
            }
        elif field_obj.type == 'html':
            # Strip HTML for cleaner text
            from odoo.tools import html2plaintext
            return html2plaintext(value) if value else None
        
        return value

    @api.model
    def _get_common_fields(self, record):
        """Get common fields to read from a record"""
        common = ['name', 'display_name', 'state', 'code']
        
        # Add model-specific common fields
        model_specific = {
            'sale.order.line': ['product_id', 'product_uom_qty', 'price_unit', 'price_subtotal', 'discount'],
            'purchase.order.line': ['product_id', 'product_qty', 'price_unit', 'price_subtotal'],
            'account.move.line': ['name', 'account_id', 'debit', 'credit', 'balance'],
            'res.partner': ['name', 'email', 'phone', 'city', 'country_id', 'is_company'],
        }
        
        if record._name in model_specific:
            return model_specific[record._name]
        
        # Return fields that exist
        return [f for f in common if hasattr(record, f)]
