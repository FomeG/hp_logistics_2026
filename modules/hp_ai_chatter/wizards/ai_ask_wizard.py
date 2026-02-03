import logging
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIAskWizard(models.TransientModel):
    """Wizard to ask AI questions about a record"""
    _name = 'ai.ask.wizard'
    _description = 'Ask AI Wizard'

    # Context
    res_model = fields.Char(string='Model', required=True)
    res_id = fields.Integer(string='Record ID', required=True)
    record_name = fields.Char(string='Record', compute='_compute_record_name')

    # Input
    question = fields.Text(string='Your Question', required=True)

    # Configuration
    template_id = fields.Many2one('ai.prompt.template', string='AI Template',
                                   domain=[('active', '=', True)])
    post_to_chatter = fields.Boolean(string='Post to Chatter', default=True,
                                      help='Post the question and answer to the record chatter')

    # Output
    answer = fields.Html(string='AI Response', readonly=True)
    has_answer = fields.Boolean(compute='_compute_has_answer')

    @api.depends('res_model', 'res_id')
    def _compute_record_name(self):
        for wizard in self:
            if wizard.res_model and wizard.res_id:
                try:
                    record = self.env[wizard.res_model].browse(wizard.res_id)
                    wizard.record_name = record.display_name if record.exists() else ''
                except Exception:
                    wizard.record_name = ''
            else:
                wizard.record_name = ''

    @api.depends('answer')
    def _compute_has_answer(self):
        for wizard in self:
            wizard.has_answer = bool(wizard.answer)

    @api.onchange('res_model')
    def _onchange_res_model(self):
        """Set default template based on model"""
        if self.res_model:
            template = self.env['ai.prompt.template'].search([
                ('target_model', '=', self.res_model),
                ('active', '=', True)
            ], limit=1)
            if template:
                self.template_id = template

    def action_ask(self):
        """Ask the AI and get a response"""
        self.ensure_one()

        if not self.question:
            raise UserError(_("Please enter a question."))

        # Get the related record
        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            raise UserError(_("The related record no longer exists."))

        # Build context from record
        record_context = self._get_record_context(record)

        # Get or create conversation
        conversation = self.env['ai.conversation'].get_or_create_conversation(
            res_model=self.res_model,
            res_id=self.res_id
        )

        # Build system prompt
        system_prompt = self._build_system_prompt(record_context)

        # Get conversation history
        history = conversation.get_context_messages()

        # Add user question to history
        conversation.add_message('user', self.question)

        try:
            # Call AI service
            ai_service = self.env['ai.service']
            result = ai_service.completion(
                messages=[{'role': 'system', 'content': system_prompt}] + history + [
                    {'role': 'user', 'content': self.question}
                ],
                template_id=self.template_id.id if self.template_id else None,
                res_model=self.res_model,
                res_id=self.res_id,
            )

            ai_response = result.get('content', '')

            # Save to conversation
            conversation.add_message('assistant', ai_response)

            # Convert to HTML and save
            self.answer = self._format_response(ai_response)

            # Optionally post to chatter
            if self.post_to_chatter and hasattr(record, 'message_post'):
                self._post_to_chatter(record, ai_response)

            # Return the same wizard to show the answer
            return {
                'name': _('AI Response'),
                'type': 'ir.actions.act_window',
                'res_model': 'ai.ask.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }

        except Exception as e:
            _logger.exception("AI request failed")
            raise UserError(_("AI request failed: %s") % str(e))

    def _get_record_context(self, record):
        """Extract context from the record"""
        context_parts = []

        # Try to get context from the record if it has the method
        if hasattr(record, '_get_ai_context'):
            return record._get_ai_context()

        # Fallback: basic context
        if hasattr(record, 'name'):
            context_parts.append(f"Name: {record.name}")
        if hasattr(record, 'state'):
            context_parts.append(f"State: {record.state}")
        if hasattr(record, 'partner_id') and record.partner_id:
            context_parts.append(f"Partner: {record.partner_id.name}")
        if hasattr(record, 'user_id') and record.user_id:
            context_parts.append(f"Responsible: {record.user_id.name}")
        if hasattr(record, 'date') and record.date:
            context_parts.append(f"Date: {record.date}")
        if hasattr(record, 'amount_total'):
            context_parts.append(f"Total Amount: {record.amount_total}")

        return "\n".join(context_parts) if context_parts else "No context available."

    def _build_system_prompt(self, record_context):
        """Build the system prompt"""
        base_prompt = """You are an AI assistant integrated into an Odoo ERP system.
You help users by answering questions about their business records.
Be concise, helpful, and accurate. If you don't know something, say so.
Always respond in the same language as the user's question."""

        if self.template_id:
            base_prompt = self.template_id.system_prompt

        return f"""{base_prompt}

Current Record Context:
{record_context}

Answer the user's question based on this context."""

    def _format_response(self, text):
        """Format AI response as HTML"""
        import html
        import re

        text = html.escape(text)

        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

        # Code
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

        # Lists
        lines = text.split('\n')
        result = []
        in_list = False
        for line in lines:
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                result.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                if line.strip():
                    result.append(f'<p>{line}</p>')
        if in_list:
            result.append('</ul>')

        return ''.join(result) if result else f'<p>{text}</p>'

    def _post_to_chatter(self, record, ai_response):
        """Post the Q&A to chatter"""
        ai_bot = self.env.ref('hp_ai_base.partner_ai_bot', raise_if_not_found=False)

        body = f"""
<div class="ai-qa-block">
    <p><strong>Question:</strong> {self.question}</p>
    <hr/>
    <p><strong>AI Response:</strong></p>
    {self._format_response(ai_response)}
</div>
"""
        record.message_post(
            body=Markup(body),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
            author_id=ai_bot.id if ai_bot else self.env.user.partner_id.id,
        )

    def action_clear_history(self):
        """Clear conversation history for this record"""
        self.ensure_one()
        conversation = self.env['ai.conversation'].search([
            ('res_model', '=', self.res_model),
            ('res_id', '=', self.res_id),
        ], limit=1)
        if conversation:
            conversation.clear_history()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Conversation history cleared.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_new_question(self):
        """Reset to ask a new question"""
        self.ensure_one()
        self.question = False
        self.answer = False

        return {
            'name': _('Ask AI Assistant'),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.ask.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
