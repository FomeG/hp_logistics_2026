import json
import logging
import time
from odoo import api, models, _
from odoo.exceptions import UserError

from .ai_tool_adapters import get_adapter, GeminiToolAdapter
from .ai_tools import ODOO_AI_TOOLS

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

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    _logger.warning("Google Generative AI library not installed. Gemini provider will not be available.")


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
            elif provider.code == 'gemini':
                result = self._call_gemini(provider, final_messages, effective_model,
                                           effective_max_tokens, effective_temperature)
            elif provider.code == 'custom':
                result = self._call_custom(provider, final_messages, effective_model,
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
    def _call_gemini(self, provider, messages, model, max_tokens, temperature):
        """Call Google Gemini API"""
        if not GEMINI_AVAILABLE:
            raise UserError(_("Google Generative AI library is not installed. Please install it with: pip install google-generativeai"))

        # Configure API key
        genai.configure(api_key=provider.api_key)

        # Create the model
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
        )

        # Convert messages to Gemini format
        # Gemini uses 'user' and 'model' roles, and system instruction is separate
        system_instruction = None
        gemini_history = []
        current_message = None

        for msg in messages:
            role = msg['role']
            content = msg['content']

            if role == 'system':
                system_instruction = content
            elif role == 'user':
                gemini_history.append({
                    'role': 'user',
                    'parts': [content]
                })
                current_message = content
            elif role == 'assistant':
                gemini_history.append({
                    'role': 'model',
                    'parts': [content]
                })

        # If there's a system instruction, create a new model with it
        if system_instruction:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_instruction,
            )

        # Start chat with history (excluding the last user message)
        chat_history = gemini_history[:-1] if len(gemini_history) > 1 else []
        chat = gemini_model.start_chat(history=chat_history)

        # Send the last user message
        response = chat.send_message(current_message or messages[-1]['content'])

        # Get token counts
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata'):
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)

        return {
            'content': response.text,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'model': model,
        }

    @api.model
    def _call_custom(self, provider, messages, model, max_tokens, temperature):
        """Call Custom API - placeholder for future implementation"""
        raise UserError(_("Custom provider is not yet implemented. Please use OpenAI, Anthropic, or Gemini."))

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

    # =========================================================================
    # FUNCTION CALLING / TOOLS SUPPORT
    # =========================================================================

    @api.model
    def completion_with_tools(self, messages, record, tools=None,
                              provider_id=None, template_id=None,
                              max_tokens=None, temperature=None, model=None,
                              res_model=None, res_id=None, max_iterations=10):
        """
        AI completion with function calling support.

        This method handles the tool calling loop:
        1. Send message to AI with tool definitions
        2. If AI wants to call tools, execute them and send results back
        3. Repeat until AI gives final text response

        Args:
            messages: List of message dicts with 'role' and 'content'
            record: The Odoo record to operate on (for tool execution)
            tools: List of tool definitions (default: ODOO_AI_TOOLS)
            max_iterations: Max tool calling iterations (safety limit)
            ... other args same as completion()

        Returns:
            dict with 'content', 'input_tokens', 'output_tokens', 'model', 'tool_calls_made'
        """
        # Get provider
        provider = self._get_provider(provider_id, template_id)
        if not provider:
            raise UserError(_("No AI provider configured. Please configure one in Settings > AI."))

        # Check if provider supports tools
        if provider.code not in ('openai', 'anthropic', 'gemini'):
            _logger.info(f"Provider {provider.code} doesn't support tools, falling back to regular completion")
            return self.completion(
                messages=messages, provider_id=provider_id, template_id=template_id,
                max_tokens=max_tokens, temperature=temperature, model=model,
                res_model=res_model, res_id=res_id
            )

        # Get adapter for this provider
        adapter = get_adapter(provider.code)
        if not adapter:
            return self.completion(
                messages=messages, provider_id=provider_id, template_id=template_id,
                max_tokens=max_tokens, temperature=temperature, model=model,
                res_model=res_model, res_id=res_id
            )

        # Use default tools if not specified
        tools = tools or ODOO_AI_TOOLS

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
            if not final_messages or final_messages[0].get('role') != 'system':
                final_messages.insert(0, {
                    'role': 'system',
                    'content': template.system_prompt
                })

        # Format tools for provider
        formatted_tools = adapter.format_tools(tools)

        # Tool execution loop
        start_time = time.time()
        total_input_tokens = 0
        total_output_tokens = 0
        tool_calls_made = []

        try:
            # Gemini needs special handling - it maintains chat session internally
            if provider.code == 'gemini':
                result = self._gemini_tool_loop(
                    provider, final_messages, effective_model,
                    effective_max_tokens, effective_temperature,
                    formatted_tools, tools, record, max_iterations
                )
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

            # OpenAI and Anthropic use message-based loop
            for iteration in range(max_iterations):
                # Call provider with tools
                if provider.code == 'openai':
                    response, raw_response = self._call_openai_with_tools(
                        provider, final_messages, effective_model,
                        effective_max_tokens, effective_temperature, formatted_tools
                    )
                elif provider.code == 'anthropic':
                    response, raw_response = self._call_anthropic_with_tools(
                        provider, final_messages, effective_model,
                        effective_max_tokens, effective_temperature, formatted_tools
                    )

                total_input_tokens += response.get('input_tokens', 0)
                total_output_tokens += response.get('output_tokens', 0)

                # Parse tool calls
                tool_calls = adapter.parse_tool_calls(raw_response)

                if not tool_calls:
                    # No tool calls, we have final response
                    response_time = int((time.time() - start_time) * 1000)

                    result = {
                        'content': response.get('content', ''),
                        'input_tokens': total_input_tokens,
                        'output_tokens': total_output_tokens,
                        'model': effective_model,
                        'tool_calls_made': tool_calls_made
                    }

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

                # Execute tool calls
                _logger.info(f"AI requested {len(tool_calls)} tool calls")

                # Add assistant message with tool calls to history
                assistant_msg = adapter.format_assistant_message_with_tool_calls(raw_response)
                final_messages.append(assistant_msg)

                # Execute each tool and add results to messages
                for tool_call in tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['arguments']
                    tool_id = tool_call['id']

                    _logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                    # Execute tool
                    executor = self.env['ai.tool.executor']
                    exec_result = executor.execute_tool(tool_name, tool_args, record)

                    tool_calls_made.append({
                        'name': tool_name,
                        'arguments': tool_args,
                        'result': exec_result
                    })

                    # Format result for provider and add to messages
                    tool_result_msg = adapter.format_tool_result(tool_id, tool_name, exec_result)
                    final_messages.append(tool_result_msg)

            # Max iterations reached
            raise UserError(_("AI tool calling exceeded maximum iterations"))

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            _logger.exception("AI completion with tools failed")

            self._log_usage(
                provider=provider,
                template=template,
                result={'content': '', 'input_tokens': total_input_tokens, 'output_tokens': total_output_tokens, 'model': effective_model},
                response_time=response_time,
                messages=final_messages,
                res_model=res_model,
                res_id=res_id,
                status='error',
                error_message=str(e)
            )
            raise UserError(_("AI request failed: %s") % str(e))

    # =========================================================================
    # PROVIDER-SPECIFIC METHODS WITH TOOLS
    # =========================================================================

    @api.model
    def _call_openai_with_tools(self, provider, messages, model, max_tokens, temperature, tools):
        """Call OpenAI API with function calling"""
        if not OPENAI_AVAILABLE:
            raise UserError(_("OpenAI library is not installed."))

        client = openai.OpenAI(
            api_key=provider.api_key,
            base_url=provider.api_base_url or None
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            tool_choice="auto"
        )

        content = response.choices[0].message.content or ''

        return {
            'content': content,
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'model': response.model,
        }, response

    @api.model
    def _call_anthropic_with_tools(self, provider, messages, model, max_tokens, temperature, tools):
        """Call Anthropic API with function calling"""
        if not ANTHROPIC_AVAILABLE:
            raise UserError(_("Anthropic library is not installed."))

        client = anthropic.Anthropic(
            api_key=provider.api_key,
            base_url=provider.api_base_url or None
        )

        # Extract system message
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
            'tools': tools,
        }
        if system_content:
            kwargs['system'] = system_content

        response = client.messages.create(**kwargs)

        # Extract text content
        content = ''
        for block in response.content:
            if hasattr(block, 'text'):
                content += block.text

        return {
            'content': content,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'model': response.model,
        }, response

    @api.model
    def _call_gemini_with_tools(self, provider, messages, model, max_tokens, temperature, tools):
        """Call Google Gemini API with function calling"""
        if not GEMINI_AVAILABLE:
            raise UserError(_("Google Generative AI library is not installed."))

        genai.configure(api_key=provider.api_key)

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Extract system instruction and build history
        system_instruction = None
        gemini_history = []
        current_parts = None

        for msg in messages:
            role = msg['role']
            content = msg.get('content', '')
            parts = msg.get('parts', [])

            if role == 'system':
                system_instruction = content
            elif role == 'user':
                gemini_history.append({
                    'role': 'user',
                    'parts': [content] if content else parts
                })
                current_parts = [content] if content else parts
            elif role == 'assistant':
                gemini_history.append({
                    'role': 'model',
                    'parts': [content] if content else parts
                })
            elif role == 'tool_results':
                # Tool results from previous iteration
                current_parts = parts

        # Create model with tools
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=system_instruction,
            tools=tools
        )

        # Start chat with history
        chat_history = gemini_history[:-1] if len(gemini_history) > 1 else []
        chat = gemini_model.start_chat(history=chat_history)

        # Send message (either user message or tool results)
        response = chat.send_message(current_parts)

        # Get token counts
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata'):
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)

        # Get text content if available
        content = GeminiToolAdapter.get_text_response(response)

        return {
            'content': content,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'model': model,
        }, response

    @api.model
    def _gemini_tool_loop(self, provider, messages, model, max_tokens, temperature,
                          formatted_tools, tools, record, max_iterations):
        """
        Handle Gemini tool calling in a continuous chat session.

        Gemini requires tool responses to immediately follow tool calls
        within the same chat session, so we handle the entire loop here.
        """
        if not GEMINI_AVAILABLE:
            raise UserError(_("Google Generative AI library is not installed."))

        genai.configure(api_key=provider.api_key)

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Extract system instruction and build history
        system_instruction = None
        gemini_history = []
        user_message = None

        for msg in messages:
            role = msg['role']
            content = msg.get('content', '')

            if role == 'system':
                system_instruction = content
            elif role == 'user':
                gemini_history.append({
                    'role': 'user',
                    'parts': [content]
                })
                user_message = content
            elif role == 'assistant':
                gemini_history.append({
                    'role': 'model',
                    'parts': [content]
                })

        # Create model with tools
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=system_instruction,
            tools=formatted_tools
        )

        # Start chat with history (excluding the last user message which we'll send)
        chat_history = gemini_history[:-1] if len(gemini_history) > 1 else []
        chat = gemini_model.start_chat(history=chat_history)

        # Tool calling loop
        total_input_tokens = 0
        total_output_tokens = 0
        tool_calls_made = []
        current_message = user_message

        for iteration in range(max_iterations):
            # Send message
            response = chat.send_message(current_message)

            # Get token counts
            if hasattr(response, 'usage_metadata'):
                total_input_tokens += getattr(response.usage_metadata, 'prompt_token_count', 0)
                total_output_tokens += getattr(response.usage_metadata, 'candidates_token_count', 0)

            # Check for function calls
            function_calls = []
            candidate = response.candidates[0] if response.candidates else None
            if candidate and candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        function_calls.append({
                            'name': fc.name,
                            'args': dict(fc.args) if fc.args else {}
                        })

            if not function_calls:
                # No function calls, get final text response
                content = GeminiToolAdapter.get_text_response(response)
                return {
                    'content': content,
                    'input_tokens': total_input_tokens,
                    'output_tokens': total_output_tokens,
                    'model': model,
                    'tool_calls_made': tool_calls_made
                }

            # Execute function calls and prepare responses
            _logger.info(f"Gemini requested {len(function_calls)} function calls")

            function_responses = []
            for fc in function_calls:
                tool_name = fc['name']
                tool_args = fc['args']

                _logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                # Execute tool
                executor = self.env['ai.tool.executor']
                exec_result = executor.execute_tool(tool_name, tool_args, record)

                tool_calls_made.append({
                    'name': tool_name,
                    'arguments': tool_args,
                    'result': exec_result
                })

                # Create function response part
                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=tool_name,
                            response={'result': json.dumps(exec_result, default=str, ensure_ascii=False)}
                        )
                    )
                )

            # Send function responses back to continue the conversation
            current_message = function_responses

        # Max iterations reached
        raise UserError(_("AI tool calling exceeded maximum iterations"))
