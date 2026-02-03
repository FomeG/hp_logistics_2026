import logging
import time
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    _logger.warning("OpenAI library not installed. OpenAI provider will not be available.")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    _logger.warning("Anthropic library not installed. Anthropic provider will not be available.")


class AIService(models.AbstractModel):
    _name = 'ai.service'
    _description = 'AI Service'

    @api.model
    def completion(self, messages, provider_id=None, template_id=None,
                   max_tokens=None, temperature=None, model=None,
                   res_model=None, res_id=None):
        """
        Main method to get AI completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            provider_id: Optional specific provider ID
            template_id: Optional template ID to use settings from
            max_tokens: Override max tokens
            temperature: Override temperature
            model: Override model name
            res_model: Related Odoo model (for logging)
            res_id: Related record ID (for logging)

        Returns:
            dict with 'content', 'input_tokens', 'output_tokens', 'model'
        """
        # Get provider
        provider = self._get_provider(provider_id, template_id)
        if not provider:
            raise UserError(_("No AI provider configured. Please configure one in Settings > AI."))

        # Get template if specified
        template = None
        if template_id:
            template = self.env['ai.prompt.template'].browse(template_id)

        # Determine parameters
        effective_model = model or (template and template.model_override) or provider.model_name
        effective_max_tokens = max_tokens or (template and template.max_tokens) or provider.default_max_tokens
        effective_temperature = temperature if temperature is not None else (
            template.temperature if template else provider.default_temperature
        )

        # Prepare messages with system prompt from template if available
        final_messages = list(messages)
        if template and template.system_prompt:
            # Insert system prompt at the beginning if not already present
            if not final_messages or final_messages[0].get('role') != 'system':
                final_messages.insert(0, {
                    'role': 'system',
                    'content': template.system_prompt
                })

        # Call the appropriate provider
        start_time = time.time()
        try:
            if provider.code == 'openai':
                result = self._call_openai(provider, final_messages, effective_model,
                                           effective_max_tokens, effective_temperature)
            elif provider.code == 'anthropic':
                result = self._call_anthropic(provider, final_messages, effective_model,
                                              effective_max_tokens, effective_temperature)
            else:
                raise UserError(_("Unknown provider: %s") % provider.code)

            response_time = int((time.time() - start_time) * 1000)

            # Log usage
            self._log_usage(
                provider=provider,
                template=template,
                result=result,
                response_time=response_time,
                messages=final_messages,
                res_model=res_model,
                res_id=res_id,
                status='success'
            )

            return result

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            _logger.exception("AI completion failed")

            # Log error
            self._log_usage(
                provider=provider,
                template=template,
                result={'content': '', 'input_tokens': 0, 'output_tokens': 0, 'model': effective_model},
                response_time=response_time,
                messages=final_messages,
                res_model=res_model,
                res_id=res_id,
                status='error',
                error_message=str(e)
            )
            raise UserError(_("AI request failed: %s") % str(e))

    @api.model
    def _get_provider(self, provider_id=None, template_id=None):
        """Get the provider to use"""
        if provider_id:
            return self.env['ai.provider'].browse(provider_id)

        if template_id:
            template = self.env['ai.prompt.template'].browse(template_id)
            if template.provider_id:
                return template.provider_id

        # Get default provider from settings
        param = self.env['ir.config_parameter'].sudo()
        default_id = param.get_param('hp_ai_base.default_provider_id')
        if default_id:
            return self.env['ai.provider'].browse(int(default_id))

        # Fallback to first active provider
        return self.env['ai.provider'].get_default_provider()

    @api.model
    def _call_openai(self, provider, messages, model, max_tokens, temperature):
        """Call OpenAI API"""
        if not OPENAI_AVAILABLE:
            raise UserError(_("OpenAI library is not installed. Please install it with: pip install openai"))

        client = openai.OpenAI(
            api_key=provider.api_key,
            base_url=provider.api_base_url or None
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return {
            'content': response.choices[0].message.content,
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'model': response.model,
        }

    @api.model
    def _call_anthropic(self, provider, messages, model, max_tokens, temperature):
        """Call Anthropic API"""
        if not ANTHROPIC_AVAILABLE:
            raise UserError(_("Anthropic library is not installed. Please install it with: pip install anthropic"))

        client = anthropic.Anthropic(
            api_key=provider.api_key,
            base_url=provider.api_base_url or None
        )

        # Extract system message for Anthropic (they handle it differently)
        system_content = None
        api_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_content = msg['content']
            else:
                api_messages.append(msg)

        kwargs = {
            'model': model,
            'messages': api_messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
        }
        if system_content:
            kwargs['system'] = system_content

        response = client.messages.create(**kwargs)

        return {
            'content': response.content[0].text,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'model': response.model,
        }

    @api.model
    def _log_usage(self, provider, template, result, response_time, messages,
                   res_model=None, res_id=None, status='success', error_message=None):
        """Log AI usage"""
        # Check if logging is enabled
        param = self.env['ir.config_parameter'].sudo()
        if not param.get_param('hp_ai_base.enable_logging', 'True') == 'True':
            return

        # Calculate cost if cost tracking is enabled
        cost = 0.0
        if param.get_param('hp_ai_base.enable_cost_tracking', 'True') == 'True':
            input_cost = (result.get('input_tokens', 0) / 1000) * (provider.input_cost_per_1k or 0)
            output_cost = (result.get('output_tokens', 0) / 1000) * (provider.output_cost_per_1k or 0)
            cost = input_cost + output_cost

        # Get prompt preview
        prompt_preview = ''
        for msg in messages:
            if msg.get('role') == 'user':
                prompt_preview = msg.get('content', '')[:500]
                break

        self.env['ai.usage.log'].create_log(
            provider_id=provider.id,
            template_id=template.id if template else False,
            model_used=result.get('model'),
            input_tokens=result.get('input_tokens', 0),
            output_tokens=result.get('output_tokens', 0),
            cost=cost,
            response_time_ms=response_time,
            res_model=res_model,
            res_id=res_id,
            prompt_preview=prompt_preview,
            response_preview=result.get('content', '')[:500],
            status=status,
            error_message=error_message,
        )

    @api.model
    def chat_completion(self, user_message, conversation_history=None,
                        system_prompt=None, **kwargs):
        """
        Convenience method for chat-style completion.

        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages
            system_prompt: Optional system prompt
            **kwargs: Additional arguments passed to completion()

        Returns:
            dict with 'content' and token info
        """
        messages = []

        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({'role': 'user', 'content': user_message})

        return self.completion(messages=messages, **kwargs)
