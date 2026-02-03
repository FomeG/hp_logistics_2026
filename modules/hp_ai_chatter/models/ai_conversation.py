import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AIConversation(models.Model):
    """
    Stores AI conversation context for each thread.
    This allows the AI to remember previous messages in the conversation.
    """
    _name = 'ai.conversation'
    _description = 'AI Conversation History'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)

    # Link to the source record
    res_model = fields.Char(string='Related Model', required=True, index=True)
    res_id = fields.Integer(string='Related Record ID', required=True, index=True)

    # Conversation data
    message_ids = fields.One2many('ai.conversation.message', 'conversation_id', string='Messages')
    message_count = fields.Integer(string='Message Count', compute='_compute_message_count')

    # Configuration
    template_id = fields.Many2one('ai.prompt.template', string='Prompt Template')
    max_context_messages = fields.Integer(string='Max Context Messages', default=10,
                                          help='Maximum number of previous messages to include in context')

    # Status
    active = fields.Boolean(string='Active', default=True)
    last_activity = fields.Datetime(string='Last Activity', default=fields.Datetime.now)

    _sql_constraints = [
        ('unique_thread', 'UNIQUE(res_model, res_id)', 'Only one conversation per thread allowed'),
    ]

    @api.depends('res_model', 'res_id')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.res_model},{record.res_id}"

    @api.depends('message_ids')
    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.message_ids)

    @api.model
    def get_or_create_conversation(self, res_model, res_id):
        """Get existing conversation or create a new one"""
        conversation = self.search([
            ('res_model', '=', res_model),
            ('res_id', '=', res_id),
            ('active', '=', True)
        ], limit=1)

        if not conversation:
            conversation = self.create({
                'res_model': res_model,
                'res_id': res_id,
            })

        return conversation

    def add_message(self, role, content):
        """Add a message to the conversation"""
        self.ensure_one()
        self.env['ai.conversation.message'].create({
            'conversation_id': self.id,
            'role': role,
            'content': content,
        })
        self.last_activity = fields.Datetime.now()

    def get_context_messages(self):
        """Get recent messages for AI context"""
        self.ensure_one()
        messages = self.message_ids.sorted('create_date')[-self.max_context_messages:]
        return [{'role': msg.role, 'content': msg.content} for msg in messages]

    def clear_history(self):
        """Clear conversation history"""
        self.ensure_one()
        self.message_ids.unlink()


class AIConversationMessage(models.Model):
    """Individual messages in an AI conversation"""
    _name = 'ai.conversation.message'
    _description = 'AI Conversation Message'
    _order = 'create_date asc'

    conversation_id = fields.Many2one('ai.conversation', string='Conversation',
                                       required=True, ondelete='cascade')
    role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ], string='Role', required=True)
    content = fields.Text(string='Content', required=True)

    # Metadata
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    token_count = fields.Integer(string='Token Count')
