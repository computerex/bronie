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
    PROMPT = \
f"""
You are a software engineer agent. Use the tools provided to do the software engineering tasks. Your token usage is being tracked.

Always use relative paths from the project directory when working with files.

Available tools:
- edit_file: Edit a file or create a new one if it doesn't exist. Do not write the code yourself just instruct the tool to do the changes by giving it high level instructions.
    - Parameters: filename, editing_instructions
- list_files: List files in a directory with line counts
    - Parameters: directory_path (defaults to current directory if not specified)
- grep_search: Search for patterns in files
    - Parameters: pattern, file_pattern (optional, defaults to all files)
- read_file: Read the contents of a file
    - Parameters: filename, start_line (optional), end_line (optional)
- search_files: Search for files by patterns
    - Parameters: regex_pattern
- talk_to_user: Talk to the user, should be the final tool call and will terminate the execution and cede control to the user.
    - Parameters: message
- exec_shell: Execute a shell command (requires user approval before execution)
    - Parameters: command

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
        "content":  PROMPT
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
