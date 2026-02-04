# -*- coding: utf-8 -*-
"""
AI Tool Adapters - Convert tool definitions to provider-specific formats

Each provider (OpenAI, Anthropic, Gemini) has slightly different formats for
function calling. This module handles the conversion.
"""

import json
import logging

_logger = logging.getLogger(__name__)


class BaseToolAdapter:
    """Base class for tool adapters"""
    
    @classmethod
    def format_tools(cls, tools):
        """Convert tool definitions to provider format"""
        raise NotImplementedError
    
    @classmethod
    def parse_tool_calls(cls, response):
        """
        Parse tool calls from provider response.
        
        Returns:
            list of dict: [{'name': 'tool_name', 'arguments': {...}, 'id': 'call_id'}, ...]
            or None if no tool calls
        """
        raise NotImplementedError
    
    @classmethod
    def format_tool_result(cls, tool_call_id, tool_name, result):
        """Format tool result for sending back to provider"""
        raise NotImplementedError


class OpenAIToolAdapter(BaseToolAdapter):
    """Adapter for OpenAI function calling format"""
    
    @classmethod
    def format_tools(cls, tools):
        """
        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "...",
                "parameters": {...}
            }
        }
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for tool in tools
        ]
    
    @classmethod
    def parse_tool_calls(cls, response):
        """Parse tool calls from OpenAI response"""
        message = response.choices[0].message
        
        if not message.tool_calls:
            return None
        
        calls = []
        for tool_call in message.tool_calls:
            calls.append({
                'id': tool_call.id,
                'name': tool_call.function.name,
                'arguments': json.loads(tool_call.function.arguments)
            })
        return calls
    
    @classmethod
    def format_tool_result(cls, tool_call_id, tool_name, result):
        """Format tool result message for OpenAI"""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(result, ensure_ascii=False, default=str)
        }
    
    @classmethod
    def format_assistant_message_with_tool_calls(cls, response):
        """Format assistant message that contains tool calls"""
        message = response.choices[0].message
        return {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ] if message.tool_calls else None
        }


class AnthropicToolAdapter(BaseToolAdapter):
    """Adapter for Anthropic (Claude) function calling format"""
    
    @classmethod
    def format_tools(cls, tools):
        """
        Anthropic format:
        {
            "name": "tool_name",
            "description": "...",
            "input_schema": {...}
        }
        """
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["parameters"]
            }
            for tool in tools
        ]
    
    @classmethod
    def parse_tool_calls(cls, response):
        """Parse tool calls from Anthropic response"""
        calls = []
        for block in response.content:
            if block.type == "tool_use":
                calls.append({
                    'id': block.id,
                    'name': block.name,
                    'arguments': block.input
                })
        
        return calls if calls else None
    
    @classmethod
    def format_tool_result(cls, tool_call_id, tool_name, result):
        """Format tool result for Anthropic"""
        return {
            "type": "tool_result",
            "tool_use_id": tool_call_id,
            "content": json.dumps(result, ensure_ascii=False, default=str)
        }
    
    @classmethod
    def format_assistant_message_with_tool_calls(cls, response):
        """Format assistant message that contains tool calls"""
        content = []
        for block in response.content:
            if block.type == "text":
                content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        return {
            "role": "assistant",
            "content": content
        }


class GeminiToolAdapter(BaseToolAdapter):
    """Adapter for Google Gemini function calling format"""
    
    @classmethod
    def format_tools(cls, tools):
        """
        Gemini format (using google.generativeai):
        Uses FunctionDeclaration objects, but we can pass dicts
        """
        # Import here to avoid dependency issues
        try:
            import google.generativeai as genai
            from google.generativeai.types import FunctionDeclaration, Tool
        except ImportError:
            _logger.warning("google-generativeai not installed")
            return None
        
        function_declarations = []
        for tool in tools:
            # Gemini uses slightly different parameter format
            func_decl = FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=cls._convert_params_to_gemini(tool["parameters"])
            )
            function_declarations.append(func_decl)
        
        return [Tool(function_declarations=function_declarations)]
    
    @classmethod
    def _convert_params_to_gemini(cls, params):
        """Convert JSON Schema to Gemini parameter format"""
        # Gemini expects a specific format for parameters
        # It's similar to JSON Schema but with some differences
        return {
            "type": "OBJECT",
            "properties": {
                name: cls._convert_property(prop)
                for name, prop in params.get("properties", {}).items()
            },
            "required": params.get("required", [])
        }
    
    @classmethod
    def _convert_property(cls, prop):
        """Convert a single property to Gemini format"""
        type_mapping = {
            "string": "STRING",
            "integer": "INTEGER",
            "number": "NUMBER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
            "object": "OBJECT"
        }
        
        result = {
            "type": type_mapping.get(prop.get("type", "string"), "STRING"),
            "description": prop.get("description", "")
        }
        
        if prop.get("type") == "array" and "items" in prop:
            result["items"] = cls._convert_property(prop["items"])
        
        return result
    
    @classmethod
    def parse_tool_calls(cls, response):
        """Parse tool calls from Gemini response"""
        # Check if response has function calls
        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content or not candidate.content.parts:
            return None
        
        calls = []
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                calls.append({
                    'id': fc.name,  # Gemini doesn't use separate IDs
                    'name': fc.name,
                    'arguments': dict(fc.args) if fc.args else {}
                })
        
        return calls if calls else None
    
    @classmethod
    def format_tool_result(cls, tool_call_id, tool_name, result):
        """Format tool result for Gemini"""
        try:
            from google.generativeai.types import Part
            from google.protobuf.struct_pb2 import Struct
            
            # Convert result to Struct
            response_struct = Struct()
            result_dict = result if isinstance(result, dict) else {'result': result}
            # Handle non-JSON-serializable values
            clean_dict = json.loads(json.dumps(result_dict, default=str))
            response_struct.update(clean_dict)
            
            return Part.from_function_response(
                name=tool_name,
                response=response_struct
            )
        except Exception as e:
            _logger.warning(f"Error formatting Gemini tool result: {e}")
            # Fallback to simple dict
            return {
                "function_response": {
                    "name": tool_name,
                    "response": result
                }
            }
    
    @classmethod
    def has_text_response(cls, response):
        """Check if response has a text part (final answer)"""
        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content or not candidate.content.parts:
            return False
        
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                return True
        return False
    
    @classmethod
    def get_text_response(cls, response):
        """Get text from response"""
        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content or not candidate.content.parts:
            return ""
        
        texts = []
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                texts.append(part.text)
        return "\n".join(texts)


# Factory to get adapter by provider code
ADAPTERS = {
    'openai': OpenAIToolAdapter,
    'anthropic': AnthropicToolAdapter,
    'gemini': GeminiToolAdapter,
}


def get_adapter(provider_code):
    """Get the appropriate adapter for a provider"""
    return ADAPTERS.get(provider_code)
