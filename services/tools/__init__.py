import inspect
import typing
import logging
from typing import Callable, Any, Dict, List, Optional, Union, get_type_hints, get_origin, get_args

# Set up logging
logger = logging.getLogger(__name__)

# Store registered tools
tool_registry: Dict[str, Dict[str, Any]] = {}

# Type mappings
_py2json = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    dict: "object",
    list: "array",
}

def _map_type(annotation: Any) -> Dict[str, Any]:
    """
    Map a Python type annotation to a JSON schema.
    Handles List, Dict, Optional, Union and basic types.
    """
    # Handle None or Any
    if annotation is None or annotation is Any:
        return {"type": "string"}
    
    # Handle typing.Optional (Union[T, None])
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        # Check if it's Optional (one of the args is None or NoneType)
        if type(None) in args:
            # Find the non-None type
            for arg in args:
                if arg is not type(None):
                    return _map_type(arg)
        # Handle regular Union
        return {"oneOf": [_map_type(arg) for arg in args]}
    
    # Handle List[T]
    if origin is list:
        item_type = get_args(annotation)[0] if get_args(annotation) else Any
        return {
            "type": "array",
            "items": _map_type(item_type)
        }
    
    # Handle Dict
    if origin is dict:
        key_type, value_type = get_args(annotation) if get_args(annotation) else (str, Any)
        return {
            "type": "object",
            "additionalProperties": _map_type(value_type)
        }
    
    # Handle Literal
    if origin is typing.Literal:
        values = get_args(annotation)
        return {
            "type": _py2json.get(type(values[0]), "string"),
            "enum": list(values)
        }
    
    # Handle basic types
    if annotation in _py2json:
        return {"type": _py2json[annotation]}
    
    # Default to string for any complex/custom types
    return {"type": "string"}

def extract_param_descriptions_from_docstring(docstring: str) -> Dict[str, str]:
    """Extract parameter descriptions from a function's docstring."""
    if not docstring:
        return {}
    
    param_desc = {}
    lines = docstring.split('\n')
    in_args_section = False
    current_param = None
    
    for line in lines:
        line = line.strip()
        if "Args:" in line:
            in_args_section = True
            continue
        
        if in_args_section:
            # Check if we've exited the Args section
            if line.startswith("Returns:") or not line:
                in_args_section = False
                continue
            
            # Check for a new parameter
            if ':' in line and not line.startswith(' '):
                parts = line.split(':', 1)
                current_param = parts[0].strip()
                description = parts[1].strip()
                param_desc[current_param] = description
            # Add to current parameter's description if we have one
            elif current_param and line:
                param_desc[current_param] += ' ' + line
    
    return param_desc

def tool(func: Callable) -> Callable:
    """
    Decorator to register a function as a tool with automatic JSON schema derivation.
    Works with both OpenAI and Google Gemini formats.
    """
    sig = inspect.signature(func)
    props: Dict[str, Any] = {}
    required: List[str] = []
    
    # Get type hints for better accuracy
    type_hints = get_type_hints(func)
    
    # Extract parameter descriptions from docstring
    docstring = inspect.getdoc(func) or ""
    param_descriptions = extract_param_descriptions_from_docstring(docstring)

    for name, param in sig.parameters.items():
        # Use type_hints if available, otherwise use parameter annotation
        ann = type_hints.get(name, param.annotation) if param.annotation is not inspect._empty else str
        
        # Get description from docstring if available
        desc = param_descriptions.get(name, f"{name} ({getattr(ann, '__name__', str(ann))})")
        
        # Create schema for this parameter
        props[name] = _map_type(ann)
        props[name]["description"] = desc
        
        if param.default is inspect._empty:
            required.append(name)

    schema: Dict[str, Any] = {
        "type": "object",
        "properties": props,
        "required": required,
    }

    # Register the tool with both function and schema
    tool_registry[func.__name__] = {
        "name": func.__name__,
        "description": docstring,
        "parameters": schema,
        "func": func,
    }
    
    logger.info(f"Registered tool: {func.__name__}")
    
    # Return the original function unchanged - important for Gemini to use it directly
    return func


def get_openai_tools() -> List[Dict[str, Any]]:
    """
    Return a list of function-schema dicts for OpenAI's function-calling API.
    """
    return [
        {"type": "function", "function": {
            "name": meta["name"], 
            "description": meta["description"], 
            "parameters": meta["parameters"]
         }}
        for meta in tool_registry.values()
    ]

def get_gemini_tools() -> List[Dict[str, Any]]:
    """
    Return a list of function-schema dicts for Google Gemini's function-calling API.
    """
    gemini_tools = []
    for meta in tool_registry.values():
        gemini_tools.append({
            "function_declarations": [{
                "name": meta["name"],
                "description": meta["description"],
                "parameters": meta["parameters"]
            }]
        })
    
    return gemini_tools
