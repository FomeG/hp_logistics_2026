from odoo import api, fields, models


class AIUsageLog(models.Model):
    _name = 'ai.usage.log'
    _description = 'AI Usage Log'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    provider_id = fields.Many2one('ai.provider', string='Provider', required=True, ondelete='cascade')
    template_id = fields.Many2one('ai.prompt.template', string='Template', ondelete='set null')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

    # Request Info
    model_used = fields.Char(string='Model Used')
    input_tokens = fields.Integer(string='Input Tokens')
    output_tokens = fields.Integer(string='Output Tokens')
    total_tokens = fields.Integer(string='Total Tokens', compute='_compute_total_tokens', store=True)

    # Cost
    cost = fields.Float(string='Cost', digits=(10, 6))
    currency_id = fields.Many2one(related='provider_id.currency_id', store=True)

    # Timing
    response_time_ms = fields.Integer(string='Response Time (ms)')

    # Context
    res_model = fields.Char(string='Related Model')
    res_id = fields.Integer(string='Related Record ID')

    # Content (for debugging/audit)
    prompt_preview = fields.Text(string='Prompt Preview', help='First 500 chars of the prompt')
    response_preview = fields.Text(string='Response Preview', help='First 500 chars of the response')

    # Status
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Status', default='success')
    error_message = fields.Text(string='Error Message')

    @api.depends('provider_id', 'create_date')
    def _compute_name(self):
        for record in self:
            if record.provider_id and record.create_date:
                record.name = f"{record.provider_id.name} - {record.create_date.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                record.name = 'New'

    @api.depends('input_tokens', 'output_tokens')
    def _compute_total_tokens(self):
        for record in self:
            record.total_tokens = (record.input_tokens or 0) + (record.output_tokens or 0)

    @api.model
    def create_log(self, provider_id, **kwargs):
        """Utility method to create a log entry"""
        vals = {
            'provider_id': provider_id,
            'user_id': self.env.user.id,
        }
        vals.update(kwargs)

        # Truncate previews
        if vals.get('prompt_preview') and len(vals['prompt_preview']) > 500:
            vals['prompt_preview'] = vals['prompt_preview'][:500] + '...'
        if vals.get('response_preview') and len(vals['response_preview']) > 500:
            vals['response_preview'] = vals['response_preview'][:500] + '...'

        return self.sudo().create(vals)
