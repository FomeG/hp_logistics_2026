import json
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AIProvider(models.Model):
    _name = 'ai.provider'
    _description = 'AI Provider Configuration'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    code = fields.Selection([
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('gemini', 'Google Gemini'),
        ('custom', 'Custom Provider'),
    ], string='Provider', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # API Configuration
    api_key = fields.Char(string='API Key', required=True, groups='base.group_system')
    api_base_url = fields.Char(
        string='API Base URL',
        help='API endpoint. Required for custom providers. Optional for standard providers.'
    )

    # Model Configuration
    model_name = fields.Char(
        string='Model Name',
        required=True,
        help='e.g., gpt-4o, gpt-4o-mini, claude-3-5-sonnet-20241022, gemini-1.5-pro'
    )

    # Custom Provider Configuration
    is_custom_config = fields.Boolean(
        string='Custom Configuration',
        default=False,
        help='Enable to customize request headers and body format'
    )
    custom_headers = fields.Text(
        string='Custom Headers (JSON)',
        help='Additional headers in JSON format, e.g., {"X-Custom-Header": "value"}'
    )
    custom_request_template = fields.Text(
        string='Request Body Template',
        help='''JSON template for request body. Use placeholders:
{model} - model name
{messages} - messages array (JSON)
{max_tokens} - max tokens
{temperature} - temperature

Example for OpenAI-compatible:
{
    "model": "{model}",
    "messages": {messages},
    "max_tokens": {max_tokens},
    "temperature": {temperature}
}'''
    )
    custom_response_content_path = fields.Char(
        string='Response Content Path',
        default='choices.0.message.content',
        help='JSON path to extract content from response. e.g., choices.0.message.content'
    )
    custom_response_input_tokens_path = fields.Char(
        string='Input Tokens Path',
        default='usage.prompt_tokens',
        help='JSON path to extract input tokens from response'
    )
    custom_response_output_tokens_path = fields.Char(
        string='Output Tokens Path',
        default='usage.completion_tokens',
        help='JSON path to extract output tokens from response'
    )

    # Auth Configuration for Custom Provider
    auth_type = fields.Selection([
        ('bearer', 'Bearer Token'),
        ('api_key_header', 'API Key in Header'),
        ('api_key_query', 'API Key in Query String'),
    ], string='Authentication Type', default='bearer')
    auth_header_name = fields.Char(
        string='Auth Header Name',
        default='Authorization',
        help='Header name for authentication. e.g., Authorization, X-API-Key'
    )
    auth_key_name = fields.Char(
        string='API Key Parameter Name',
        default='key',
        help='Query parameter name for API key (when using API Key in Query String)'
    )

    # Default Parameters
    default_max_tokens = fields.Integer(string='Default Max Tokens', default=2048)
    default_temperature = fields.Float(string='Default Temperature', default=0.7)

    # Rate Limiting
    requests_per_minute = fields.Integer(string='Requests/Minute Limit', default=60)
    tokens_per_minute = fields.Integer(string='Tokens/Minute Limit', default=100000)

    # Cost Tracking
    input_cost_per_1k = fields.Float(string='Input Cost per 1K tokens', digits=(10, 6))
    output_cost_per_1k = fields.Float(string='Output Cost per 1K tokens', digits=(10, 6))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Statistics
    total_requests = fields.Integer(string='Total Requests', compute='_compute_statistics')
    total_tokens = fields.Integer(string='Total Tokens Used', compute='_compute_statistics')
    total_cost = fields.Float(string='Total Cost', compute='_compute_statistics', digits=(10, 4))

    @api.onchange('code')
    def _onchange_code(self):
        """Set default values based on provider type"""
        if self.code == 'openai':
            self.api_base_url = ''
            self.auth_type = 'bearer'
        elif self.code == 'anthropic':
            self.api_base_url = ''
            self.auth_type = 'api_key_header'
            self.auth_header_name = 'x-api-key'
        elif self.code == 'gemini':
            self.api_base_url = 'https://generativelanguage.googleapis.com/v1beta'
            self.auth_type = 'api_key_query'
            self.auth_key_name = 'key'
        elif self.code == 'custom':
            self.is_custom_config = True

    @api.constrains('custom_headers')
    def _check_custom_headers(self):
        for record in self:
            if record.custom_headers:
                try:
                    json.loads(record.custom_headers)
                except json.JSONDecodeError:
                    raise ValidationError(_('Custom Headers must be valid JSON'))

    @api.constrains('custom_request_template')
    def _check_custom_request_template(self):
        for record in self:
            if record.custom_request_template:
                # Just check if it's valid JSON structure (with placeholders replaced)
                test_template = record.custom_request_template.replace(
                    '{model}', '"test"'
                ).replace(
                    '{messages}', '[]'
                ).replace(
                    '{max_tokens}', '100'
                ).replace(
                    '{temperature}', '0.7'
                )
                try:
                    json.loads(test_template)
                except json.JSONDecodeError:
                    raise ValidationError(_('Request Body Template must be valid JSON'))

    @api.depends('code')
    def _compute_statistics(self):
        for record in self:
            logs = self.env['ai.usage.log'].search([('provider_id', '=', record.id)])
            record.total_requests = len(logs)
            record.total_tokens = sum(logs.mapped('total_tokens'))
            record.total_cost = sum(logs.mapped('cost'))

    def test_connection(self):
        """Test the connection to the AI provider"""
        self.ensure_one()
        try:
            ai_service = self.env['ai.service']
            response = ai_service.completion(
                provider_id=self.id,
                messages=[{'role': 'user', 'content': 'Say "Connection successful!" in exactly those words.'}],
                max_tokens=50
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _('Successfully connected to %s! Response: %s') % (self.name, response.get('content', '')),
                    'type': 'success',
                    'sticky': False,
                }
            }


            
        except Exception as e:
            _logger.exception("AI Provider connection test failed")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    @api.model
    def get_default_provider(self):
        """Get the default (first active) provider"""
        return self.search([('active', '=', True)], limit=1)

    def get_parsed_custom_headers(self):
        """Get custom headers as dict"""
        self.ensure_one()
        if self.custom_headers:
            try:
                return json.loads(self.custom_headers)
            except json.JSONDecodeError:
                return {}
        return {}
