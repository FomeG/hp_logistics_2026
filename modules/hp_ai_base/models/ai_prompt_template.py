from odoo import api, fields, models, _


class AIPromptTemplate(models.Model):
    _name = 'ai.prompt.template'
    _description = 'AI Prompt Template'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, help='Unique code to reference this template in code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # Template Content
    system_prompt = fields.Text(
        string='System Prompt',
        required=True,
        help='The system prompt that sets the AI behavior and context'
    )
    user_prompt_template = fields.Text(
        string='User Prompt Template',
        help='Optional template for user prompts. Use {variable_name} for placeholders.'
    )

    # Configuration
    provider_id = fields.Many2one(
        'ai.provider',
        string='Preferred Provider',
        help='If set, this provider will be used for this template. Otherwise, default provider is used.'
    )
    model_override = fields.Char(
        string='Model Override',
        help='Override the provider default model for this template'
    )
    max_tokens = fields.Integer(string='Max Tokens', default=2048)
    temperature = fields.Float(string='Temperature', default=0.7)

    # Categorization
    category = fields.Selection([
        ('general', 'General'),
        ('sales', 'Sales'),
        ('logistics', 'Logistics'),
        ('customer_service', 'Customer Service'),
        ('analysis', 'Analysis'),
        ('document', 'Document Processing'),
    ], string='Category', default='general')

    # Model Targeting
    target_model = fields.Char(
        string='Target Model',
        help='Odoo model this template is designed for (e.g., sale.order, trucking.planning.trip)'
    )

    # Context Fields
    context_fields = fields.Text(
        string='Context Fields',
        help='Comma-separated list of fields to include in context (e.g., name,partner_id.name,state)'
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Template code must be unique!'),
    ]

    def render_system_prompt(self, context=None):
        """Render the system prompt with optional context"""
        self.ensure_one()
        prompt = self.system_prompt
        if context:
            try:
                prompt = prompt.format(**context)
            except KeyError:
                pass  # Ignore missing keys
        return prompt

    def render_user_prompt(self, context=None):
        """Render the user prompt template with context"""
        self.ensure_one()
        if not self.user_prompt_template:
            return None
        prompt = self.user_prompt_template
        if context:
            try:
                prompt = prompt.format(**context)
            except KeyError:
                pass
        return prompt

    def get_context_from_record(self, record):
        """Extract context from a record based on context_fields"""
        self.ensure_one()
        if not self.context_fields:
            return {}

        context = {}
        fields_list = [f.strip() for f in self.context_fields.split(',')]

        for field_path in fields_list:
            try:
                value = record
                for part in field_path.split('.'):
                    value = getattr(value, part)
                # Convert recordset to name if applicable
                if hasattr(value, 'name'):
                    value = value.name
                elif hasattr(value, 'display_name'):
                    value = value.display_name
                context[field_path.replace('.', '_')] = value
            except (AttributeError, KeyError):
                context[field_path.replace('.', '_')] = ''

        return context

    @api.model
    def get_template_by_code(self, code):
        """Get a template by its unique code"""
        return self.search([('code', '=', code), ('active', '=', True)], limit=1)
