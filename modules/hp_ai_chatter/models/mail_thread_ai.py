import logging
import re
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailThreadAI(models.AbstractModel):
    """
    Mixin to add AI capabilities to any model with mail.thread.
    The AI Bot will respond when mentioned in chatter messages.
    """
    _name = 'mail.thread.ai'
    _description = 'AI-enabled Mail Thread'

    # Can be overridden in inheriting models
    ai_enabled = fields.Boolean(string='AI Enabled', default=True, compute='_compute_ai_enabled')
    ai_template_id = fields.Many2one('ai.prompt.template', string='AI Template',
                                      compute='_compute_ai_template')

    def _compute_ai_enabled(self):
        """Override to control AI availability per record"""
        for record in self:
            record.ai_enabled = True

    def _compute_ai_template(self):
        """Override to set a specific template for this model"""
        default_template = self.env.ref('hp_ai_base.prompt_template_general_assistant', raise_if_not_found=False)
        for record in self:
            record.ai_template_id = default_template

    def _get_ai_context(self):
        """
        Get context about the current record for AI.
        Override this method in specific models to provide relevant context.
        """
        self.ensure_one()
        context_parts = []

        # Basic record info
        if hasattr(self, 'name'):
            context_parts.append(f"Record: {self.name}")
        if hasattr(self, 'state'):
            context_parts.append(f"State: {self.state}")
        if hasattr(self, 'partner_id') and self.partner_id:
            context_parts.append(f"Partner: {self.partner_id.name}")

        # Get fields from template if configured
        if self.ai_template_id and self.ai_template_id.context_fields:
            template_context = self.ai_template_id.get_context_from_record(self)
            for key, value in template_context.items():
                if value:
                    context_parts.append(f"{key}: {value}")

        return "\n".join(context_parts) if context_parts else "No additional context available."

    def action_ask_ai(self):
        """Open a wizard to ask AI about this record"""
        self.ensure_one()
        return {
            'name': _('Ask AI Assistant'),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.ask.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }

    def _process_ai_mention(self, message_content, author_id):
        """
        Process a message that mentions the AI bot.
        Called when a user mentions @AI Assistant in chatter.
        """
        self.ensure_one()

        if not self.ai_enabled:
            return

        # Get AI Bot partner
        ai_bot = self._get_ai_bot_partner()
        if not ai_bot:
            _logger.warning("AI Bot partner not configured")
            return

        # Clean the message (remove the mention)
        clean_content = self._clean_ai_mention(message_content)
        if not clean_content.strip():
            return

        # Get or create conversation
        conversation = self.env['ai.conversation'].get_or_create_conversation(
            res_model=self._name,
            res_id=self.id
        )

        # Build context
        record_context = self._get_ai_context()
        system_prompt = self._build_system_prompt(record_context)

        # Get conversation history
        history = conversation.get_context_messages()

        # Add current user message to history
        conversation.add_message('user', clean_content)

        try:
            # Call AI service
            ai_service = self.env['ai.service']
            result = ai_service.completion(
                messages=history + [{'role': 'user', 'content': clean_content}],
                template_id=self.ai_template_id.id if self.ai_template_id else None,
                res_model=self._name,
                res_id=self.id,
            )

            ai_response = result.get('content', '')

            # Save AI response to conversation
            conversation.add_message('assistant', ai_response)

            # Post AI response to chatter
            self._post_ai_response(ai_response, ai_bot)

        except Exception as e:
            _logger.exception("AI response failed")
            error_msg = _("Sorry, I encountered an error: %s") % str(e)
            self._post_ai_response(error_msg, ai_bot, is_error=True)

    def _get_ai_bot_partner(self):
        """Get the AI Bot partner"""
        return self.env.ref('hp_ai_base.partner_ai_bot', raise_if_not_found=False)

    def _clean_ai_mention(self, content):
        """Remove AI mention from message content"""
        # Remove @AI Assistant or similar mentions
        ai_bot = self._get_ai_bot_partner()
        if ai_bot:
            # Remove HTML mention tags
            pattern = rf'<a[^>]*href="[^"]*res\.partner[^"]*{ai_bot.id}[^"]*"[^>]*>@?[^<]*</a>'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            # Remove plain text mentions
            content = re.sub(r'@AI\s*Assistant', '', content, flags=re.IGNORECASE)
        return content.strip()

    def _build_system_prompt(self, record_context):
        """Build the system prompt with record context"""
        base_prompt = ""
        if self.ai_template_id:
            base_prompt = self.ai_template_id.system_prompt

        context_section = f"""

Current Record Context:
{record_context}

Instructions:
- Answer questions about this specific record
- Be helpful and concise
- If you don't have enough information, say so
- Respond in the same language as the user's message
"""
        return base_prompt + context_section

    def _post_ai_response(self, content, ai_bot, is_error=False):
        """Post AI response as a message in chatter"""
        self.ensure_one()

        # Convert markdown-like content to HTML for better display
        html_content = self._convert_to_html(content)

        if is_error:
            html_content = f'<p style="color: #dc3545;">{html_content}</p>'

        self.with_context(mail_create_nosubscribe=True).message_post(
            body=Markup(html_content),
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            author_id=ai_bot.id,
        )

    def _convert_to_html(self, text):
        """Convert plain text to basic HTML"""
        if not text:
            return ""

        # Escape HTML
        import html
        text = html.escape(text)

        # Convert markdown-style formatting
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

        # Italic: *text* or _text_
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)

        # Code: `code`
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

        # Line breaks
        text = text.replace('\n', '<br/>')

        return f'<p>{text}</p>'


class MailMessage(models.Model):
    """Extend mail.message to detect AI mentions"""
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)

        for message in messages:
            # Check if this message mentions the AI bot
            if message.model and message.res_id and message.body:
                self._check_ai_mention(message)

        return messages

    def _check_ai_mention(self, message):
        """Check if message mentions AI bot and trigger response"""
        ai_bot = self.env.ref('hp_ai_base.partner_ai_bot', raise_if_not_found=False)
        if not ai_bot:
            return

        # Check if AI bot is mentioned in partner_ids
        if ai_bot.id in message.partner_ids.ids:
            # Get the related record
            try:
                record = self.env[message.model].browse(message.res_id)
                if record.exists() and hasattr(record, '_process_ai_mention'):
                    # Process in a new transaction to avoid blocking
                    record.with_delay() if hasattr(record, 'with_delay') else record._process_ai_mention(
                        message.body,
                        message.author_id.id
                    )
            except Exception as e:
                _logger.exception("Failed to process AI mention: %s", e)
