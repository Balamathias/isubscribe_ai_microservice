from typing import List, Dict, Any, Optional

from services.ai_client import google_client as genai
from google.genai import types
from functools import partial

from services.functions.plans import (
    get_best_data_plans, 
    get_super_data_plans,
    get_best_data_plans_by_service,
    get_super_data_plans_by_service,
    filter_super_data_plans,
    filter_best_data_plans,
)

from services.functions.user import (
    get_user_info,
    # get_user_info_declaration
)

# DECLARATION_TOOLS = types.Tool(function_declarations=[get_user_info_declaration])


BASE_TOOLS = [
    get_best_data_plans,
    get_super_data_plans,
    get_best_data_plans_by_service,
    get_super_data_plans_by_service,
    filter_super_data_plans,
    filter_best_data_plans,
    get_user_info,
]

def bind_tools_with_user(tools, user):
    """
    Wrap only the tools marked with `_requires_user` so they
    get called as fn(user, **kwargs).
    """
    bound = []
    for fn in tools:
        if getattr(fn, "_requires_user", False):
            bound.append(partial(fn, user))
        else:
            bound.append(fn)
    return bound


def run_ai_agent(user_input: Optional[str] = None,
                 history: Optional[List[Dict]] = None,
                 model: str = "gemini-2.0-flash", request: Any | None = None) -> Dict[str, Any]:
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
    from core.context import AgentContext

    user = getattr(request, "user", None)

    AgentContext.set_current_user(user)

    tools = BASE_TOOLS

    config = types.GenerateContentConfig(tools=tools)

    contents = []
    messages = history.copy() if history else []

    system_content = types.Content(
        role="model",
        parts=[types.Part(text="You are a helpful isubscribe assistant. You have access to a variety of tools to assist users with their data and airtime plans. Please provide accurate and helpful responses.")],
    )

    history_contents = [
        types.Content(
            role=msg["role"],
            parts=[types.Part(text=msg["content"])]
        )
        for msg in messages
    ]

    contents = [system_content] + history_contents
    if user_input:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
        )

    try:
        response = genai.models.generate_content(
            model=model,
            config=config,
            contents=contents
        )

        # print(f"Response: {response}")

        # tool_call = response.candidates[0].content.parts[0].function_call

        # print(f"Tool call: {tool_call}")

        # if tool_call and tool_call.name == "get_user_info":
        #     result = get_user_info(user.id)

        #     print(f"Tool result: {result}")

        #     function_response_part = types.Part.from_function_response(
        #         name=tool_call.name,
        #         response={"result": result},
        #     )

        #     # Append function call and result of the function execution to contents
        #     contents.append(types.Content(role="model", parts=[types.Part(function_call=tool_call)])) # Append the model's function call message
        #     contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response

        #     try:
        #         final_response = genai.models.generate_content(
        #             model=model,
        #             config=config,
        #             contents=contents,
        #         )

        #         return {
        #             "tool_call": tool_call,
        #             "tool_result": result,
        #             "content": final_response.text
        #         }
        #     except Exception as e:
        #         print(f"Error in final response generation: {e}")
        #         return {"error": str(e)}

        return {"content": response.text}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
