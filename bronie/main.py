import sys
import os
from dotenv import load_dotenv
from .core.agent import Agent
from . import token_tracker
import typer

load_dotenv()

def get_agent_system_prompt():
    from .tools.registry import TOOLS
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
You are a software engineer hired with a very handsome salary. You are eager to impress your boss and get a promotion. Use the tools provided to do the software engineering tasks.

To begin, use the `list_files` tool to understand the project structure.

Always use relative paths from the project directory when working with files.

Note: The edit_file tool doesn't know about rest of code base so pass it everything necessary to make the changes as part of the instructions. You must pass all of the specifics of the instructions to the edit_file tool.

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

Say nothing but the JSON object. Always use talk_to_user tool to talk. Don't talk until all the work is done.
"""
    return {
        "role": "system",
        "content": PROMPT
    }

app = typer.Typer()

@app.command()
def main(project_dir: str = typer.Argument(None, help="The project directory to work in.")):
    """Main entry point - simplified to just setup and run agent"""
    if project_dir is not None:
        os.chdir(project_dir)
    
    agent = Agent(project_dir=project_dir, get_agent_system_prompt=get_agent_system_prompt)
    agent.run()
    
    # Show final token usage summary
    input_tokens, output_tokens = token_tracker.get_totals()
    if input_tokens > 0 or output_tokens > 0:
        print(f"\n🎯 Final Session Token Usage:")
        print(f"   Input tokens:  {input_tokens:,}")
        print(f"   Output tokens: {output_tokens:,}")
        print(f"   Total tokens:  {input_tokens + output_tokens:,}")
        print("=" * 50)
    else:
        print("\nToken tracking not available (no usage data from API)")

if __name__ == "__main__":
    app()
