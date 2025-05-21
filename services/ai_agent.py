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
)


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
    user = getattr(request, "user", None)

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
        return {"content": response.text}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
