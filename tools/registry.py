import os
import importlib
import inspect
from typing import Dict, Callable, Any, List, Optional

# Dynamic tool discovery
def discover_tools() -> Dict[str, Callable]:
    """
    Dynamically discover available tool functions in the tools directory.
    
    Scans the tools directory for .py files (excluding __init__.py and registry.py itself).
    For each module, looks for a function whose name matches the file name (minus .py).
    Each tool must provide a top-level function with the same name as its filename.
    """
    tools_dir = os.path.dirname(__file__)
    tools = {}
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename not in ['__init__.py', 'registry.py', 'config.py', 'clipboard_image.py', 'llm.py']:
            module_name = filename[:-3]  # Remove .py extension
            try:
                # Import the module
                module = importlib.import_module(f'tools.{module_name}')
                
                # Look for a function with the same name as the module
                if hasattr(module, module_name):
                    tool_function = getattr(module, module_name)
                    if callable(tool_function):
                        tools[module_name] = tool_function
                        print(f"✅ Registered tool: {module_name}")
                    else:
                        print(f"⚠️  {module_name} exists but is not callable")
                else:
                    print(f"⚠️  No function named '{module_name}' found in {filename}")
                    
            except ImportError as e:
                print(f"❌ Failed to import {filename}: {e}")
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
    
    return tools

# Build the TOOLS dictionary dynamically
TOOLS = discover_tools()

def dispatch_tool(name: str, **kwargs) -> Any:
    """
    Dispatch a tool call - exactly the same as current if-else chain.
    
    Handles parameter mapping for tools that have different parameter names
    than what the AI expects.
    """
    if name not in TOOLS:
        # Gracefully handle unknown tools instead of crashing the program.
        # Log a warning and return a structured error so the caller can
        # decide how to surface it to the user.
        warning_msg = f"⚠️ Unknown tool requested: {name} – skipping"
        print(warning_msg)
        return {"error": warning_msg}
    
    tool_function = TOOLS[name]
    
    # No parameter mapping needed – tool signatures are now consistent
    
    # Get the function signature to validate parameters
    try:
        sig = inspect.signature(tool_function)
        # Filter kwargs to only include parameters that the function accepts
        filtered_kwargs = {}
        for param_name, param_value in kwargs.items():
            if param_name in sig.parameters:
                filtered_kwargs[param_name] = param_value
            else:
                print(f"⚠️  Parameter '{param_name}' not accepted by {name}, ignoring")
        
        return tool_function(**filtered_kwargs)
    except Exception as e:
        print(f"❌ Error calling {name}: {e}")
        raise 
