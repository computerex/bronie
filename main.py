import base64
import json
import signal
import sys
import time
import tiktoken
from openai import OpenAI
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.panel import Panel
from llm import complete_chat, complete_chat_stream
from tools.edit_file import edit_file
from tools.list_files import list_files
from tools.grep_search import grep_search
from tools.read_file import read_file
from tools.search_files import search_files
from tools.talk_to_user import talk_to_user
from tools.exec_shell import exec_shell
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

load_dotenv()


def get_agent_system_prompt():
    PROMPT = \
f"""
You are a software engineer agent. Use the tools provided to do the software engineering tasks.

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

# Create global console instance
console = Console()

def count_tokens(messages):
    encoding = tiktoken.encoding_for_model("gpt-4")
    num_tokens = 0
    for message in messages:
        # Count tokens in the message content
        if isinstance(message["content"], str):
            num_tokens += len(encoding.encode(message["content"]))
        elif isinstance(message["content"], list):
            # Handle list of content (e.g., assistant responses)
            for content in message["content"]:
                if isinstance(content, dict) and "text" in content:
                    num_tokens += len(encoding.encode(content["text"]))
    return num_tokens

def main(project_dir=None):
    last_interrupt_time = 0
    multiline_mode = [False]
    
    if project_dir:
        os.chdir(project_dir)
        
    messages = [
        get_agent_system_prompt()
    ]
    
    while True:
        try:
            token_count = count_tokens(messages)
            console.print(f"[cyan]Token count:[/] {token_count}")
            mode_text = "[green]Multiline[/]" if multiline_mode[0] else "[blue]Single-line[/]"
            console.print(Panel(
                "[bold]Enter your message below[/]\n"
                f"Current mode: {mode_text}\n"
                "[dim]Available commands:\n"
                "- [bold]:m[/bold] to toggle input mode\n"
                "- [bold]:clear[/bold] to reset message history\n"
                "- [bold]:end[/bold] on a new line when finished in multiline mode",
                title="Input Instructions",
                border_style="green"
            ))
            
            lines = []
            mode_switched = False
            while True:
                try:
                    # Use simple prompt for each line
                    line = prompt('')
                    
                    line_stripped = line.strip()
                    if line_stripped == ":m":
                        multiline_mode[0] = not multiline_mode[0]
                        mode_name = "multiline" if multiline_mode[0] else "single-line"
                        console.print(f"[green]Switched to {mode_name} mode[/]")
                        mode_switched = True
                        break
                    
                    if line_stripped == ":clear":
                        messages = [get_agent_system_prompt()]
                        console.print("[green]Message history cleared[/]")
                        mode_switched = True
                        break
                        
                    if multiline_mode[0]:
                        if line.strip() == ":end":
                            if lines:
                                break  # End multiline input
                            else:
                                console.print("[yellow]Empty input, please try again[/]")
                                continue
                        else:
                            lines.append(line)
                    else:
                        lines = [line]
                        break
                        
                except KeyboardInterrupt:
                    current_time = time.time()
                    if current_time - last_interrupt_time < 1:
                        console.print("\n[red]Double interrupt detected - exiting[/]")
                        sys.exit(0)
                    last_interrupt_time = current_time
                    console.print("\n[yellow]Press Ctrl+C again within 1 second to exit[/]")
                    continue
            
            if mode_switched:
                continue  # Skip processing when just toggling modes

            if not lines:  # Handle empty input
                console.print("[yellow]Empty input, please try again[/]")
                continue
            
            user_input = "\n".join(lines)
            messages.append({"role": "user", "content": user_input})
            terminate = False
            while True:
                # Try streaming first for better user experience, fall back to regular completion if needed
                try:
                    response = ""
                    for chunk in complete_chat_stream(messages=messages, response_format={
                        "type": "json_object"
                    }, model="openai/gpt-4.1"):
                        if chunk:
                            sys.stdout.write(chunk)
                            sys.stdout.flush()
                            response += chunk
                    print()  # New line after streaming completes
                except Exception as e:
                    console.print("[yellow]Streaming failed, falling back to regular completion[/]")
                    response = complete_chat(messages=messages, response_format={
                        "type": "json_object"
                    }, model="openai/gpt-4.1")
                    console.print(Markdown(response))
                try:
                    response_json = json.loads(response)
                    messages.append({"role": "assistant", "content": [{"type": "text", "text": response}]})
                except json.JSONDecodeError:
                    console.print("[bold red]Invalid JSON response[/]", style="error")
                    sys.exit(1)
                    continue

                if "tool_calls" in response_json:
                    for tool_call in response_json["tool_calls"]:
                        #print(tool_call, flush=True)
                        if tool_call["name"] == "edit_file":
                            tool_result = edit_file(tool_call["parameters"]["filename"], tool_call["parameters"]["editing_instructions"])
                        elif tool_call["name"] == "list_files":
                            tool_result = list_files(tool_call["parameters"].get("directory_path", "."))
                        elif tool_call["name"] == "grep_search":
                            tool_result = grep_search(tool_call["parameters"]["pattern"], tool_call["parameters"].get("file_pattern", "*"))
                        elif tool_call["name"] == "read_file":
                            tool_result = read_file(tool_call["parameters"]["filename"], tool_call["parameters"].get("start_line"), tool_call["parameters"].get("end_line"))
                        elif tool_call["name"] == "search_files":
                            tool_result = search_files(tool_call["parameters"]["regex_pattern"])
                        elif tool_call["name"] == "talk_to_user":
                            tool_result = talk_to_user(tool_call["parameters"]["message"])
                        elif tool_call["name"] == "exec_shell":
                            tool_result = exec_shell(tool_call["parameters"]["command"])
                        messages.append({"role": "assistant", "content": [{"type": "text", "text": json.dumps(tool_result)}]})
                        if tool_call["name"] == "talk_to_user":
                            if isinstance(tool_result, dict) and "type" in tool_result and "content" in tool_result:
                                if tool_result["type"] == "markdown":
                                    console.print(Markdown(tool_result["content"]))
                                elif tool_result["type"] == "panel":
                                    console.print(Panel(tool_result["content"]))
                            terminate = True
                            break
                        elif isinstance(tool_result, dict) and "formatted_output" in tool_result:
                            console.print(Markdown(tool_result["formatted_output"]))
                        elif isinstance(tool_result, str):
                            console.print(Markdown(tool_result))
                        else:
                            console.print(Pretty(tool_result))

                if terminate:
                    break

        except KeyboardInterrupt:
            console.print("\n[red]Interrupt detected - exiting[/]")
            sys.exit(0)

if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else None
    main(project_dir)
