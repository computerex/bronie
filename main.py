import sys
import os
from dotenv import load_dotenv
from core.agent import Agent
import token_state

load_dotenv()

def track_tokens(arg1, arg2=None):
    """Track token usage.
    Can be called as track_tokens(prompt_tokens, completion_tokens)
    or track_tokens(response_data_dict_with_usage).
    """
    # Determine call signature
    if arg2 is None:
        # Called with response_data dict
        response_data = arg1 if isinstance(arg1, dict) else {}
        usage = response_data.get('usage', {}) if response_data else {}
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
    else:
        # Called with explicit ints
        prompt_tokens = int(arg1)
        completion_tokens = int(arg2)
    
    # Debug
    
    token_state.input_tokens += prompt_tokens
    token_state.output_tokens += completion_tokens

def get_agent_system_prompt():
    from tools.registry import TOOLS
    import inspect

    # Dynamically generate tool descriptions
    tool_descriptions = []
    for tool_name, tool_func in TOOLS.items():
        # Get function signature and docstring
        signature = inspect.signature(tool_func)
        docstring = inspect.getdoc(tool_func) or 'No description available'
    
        # Generate parameter descriptions with types and default values
        param_descriptions = []
        for param_name, param in signature.parameters.items():
            # Determine type hint
            type_hint = param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'Any'
        
            # Determine default value
            if param.default != inspect.Parameter.empty:
                default_str = f" (default: {repr(param.default)})"
            else:
                default_str = ""
        
            param_desc = f"{param_name}: {type_hint}{default_str}"
            param_descriptions.append(param_desc)
    
        # Create comprehensive tool description
        tool_desc = f"- {tool_name}:\n    {docstring}\n    - Parameters:\n      {chr(10).join('      ' + pd for pd in param_descriptions)}"
    
        tool_descriptions.append(tool_desc)

    PROMPT = f"""
You are a software engineer agent. Use the tools provided to do the software engineering tasks. Your token usage is being tracked.

Always use relative paths from the project directory when working with files.

Available tools:
{chr(10).join(tool_descriptions)}

You are responsible for all the work. Use available tools to explore the codebase and make changes.

Use this JSON object to respond:
{{
    "tool_calls": [
        {{
            "name": "tool_name",
            "parameters": {{
                "parameter_name": "value"
            }}
        }}
    ]
}}

"""
    return {
        "role": "system",
        "content": PROMPT
    }

def main(project_dir=None):
    """Main entry point - simplified to just setup and run agent"""
    if project_dir:
        os.chdir(project_dir)
    
    agent = Agent(project_dir=project_dir, get_agent_system_prompt=get_agent_system_prompt)
    agent.run()
    
    # Show final token usage summary
    if token_state.input_tokens > 0 or token_state.output_tokens > 0:
        print(f"\n🎯 Final Session Token Usage:")
        print(f"   Input tokens:  {token_state.input_tokens:,}")
        print(f"   Output tokens: {token_state.output_tokens:,}")
        print(f"   Total tokens:  {token_state.input_tokens + token_state.output_tokens:,}")
        print("=" * 50)
    else:
        print("\nToken tracking not available (no usage data from API)")

if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else None
    main(project_dir)
