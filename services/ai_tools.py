import os
import json
from typing import Optional, List, Dict, Any, Union

from services.tools import get_openai_tools, get_gemini_tools, tool_registry
from services.ai_client import openai_client as openai, google_client as gemini


def run_ai_agent(user_input: Optional[str] = None,
                 history: Optional[List[Dict]] = None,
                 model: str = "gemini-2.0-flash") -> Dict[str, Any]:
    """
    Run the AI agent using function calling with registered tools.
    Supports both OpenAI and Google Gemini APIs.

    Args:
        user_input: A new user message to append to history.
        history: Optional list of dicts [{'role':..., 'content':...}] to use as chat context.
        model: The model to use.

    Returns:
        Dict with either content or tool_result keys depending on the AI's response.
    """
    # Build messages list
    messages = history.copy() if history else []
    if user_input:
        messages.append({"role": "user", "content": user_input})

    # Determine if we're using OpenAI or Gemini based on the model
    is_openai_model = not model.startswith("gemini")

    try:
        if is_openai_model:
            # Call OpenAI API
            functions = get_openai_tools()
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                functions=functions,
                function_call="auto",
            )
            message = response.choices[0].message

            # If the model chose to call a function
            if message.function_call:
                return handle_function_call(message.function_call)
            
            # Return plain text response
            return {"content": message.content or ""}
        else:
            # Call Gemini API using Google's native format
            formatted_history = format_messages_for_gemini(messages)
            tools = get_gemini_tools()
            
            gemini_model = gemini.get_model(model)
            chat = gemini_model.start_chat(history=formatted_history)
            
            response = chat.send_message(
                user_input or "",
                tools=tools,
                tool_config={"function_calling_config": {"mode": "AUTO"}}
            )
            
            # Check if function was called
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        function_name = part.function_call.name
                        function_args = json.loads(part.function_call.args)
                        
                        # Create a standard format that mimics OpenAI's format for consistency
                        function_call_obj = {
                            "name": function_name,
                            "arguments": json.dumps(function_args)
                        }
                        
                        return handle_function_call(function_call_obj)
                
                # No function call, return text content
                return {"content": response.text}
            
            return {"content": "No response generated", "error": True}
    
    except Exception as e:
        return {
            "content": f"An error occurred: {str(e)}",
            "error": True
        }

def handle_function_call(function_call):
    """Helper to process a function call from either OpenAI or Gemini."""
    func_name = function_call.name if hasattr(function_call, 'name') else function_call.get('name')
    args_str = function_call.arguments if hasattr(function_call, 'arguments') else function_call.get('arguments', '{}')
    
    try:
        args = json.loads(args_str)
        if func_name not in tool_registry:
            return {
                "content": f"Error: Function '{func_name}' is not available.",
                "error": True
            }
            
        result = tool_registry[func_name]["func"](**args)
        
        return {
            "content": f"Executed {func_name}",
            "tool_call": {
                "name": func_name,
                "arguments": args
            },
            "tool_result": result
        }
    except json.JSONDecodeError:
        return {
            "content": "Error: Invalid function arguments format.",
            "error": True
        }
    except Exception as e:
        return {
            "content": f"Error executing {func_name}: {str(e)}",
            "error": True
        }

def format_messages_for_gemini(messages):
    """Convert OpenAI-style chat messages to Gemini format."""
    formatted = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")
        
        # In Gemini format, 'user' stays as 'user', 'assistant' becomes 'model'
        if role == "assistant":
            role = "model"
        
        # Skip function messages as they're handled differently in Gemini
        if role == "function":
            continue
            
        formatted.append({
            "role": role,
            "parts": [{"text": content}]
        })
    
    return formatted
