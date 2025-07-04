import base64
import json
import sys
import time
from openai import OpenAI
import os
from dotenv import load_dotenv
from llm import complete_chat
from tools.edit_file import edit_file
from tools.list_files import list_files
from tools.grep_search import grep_search
from tools.read_file import read_file
from tools.search_files import search_files
from tools.talk_to_user import talk_to_user

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
    if project_dir:
        # Change to the project directory if provided
        os.chdir(project_dir)
        
    messages = [
        get_agent_system_prompt()
    ]
    while True:
        user_input = input("Enter a message: ")
        messages.append({"role": "user", "content":  user_input})
        terminate = False
        while True:
            response = complete_chat(messages=messages, response_format={
                "type": "json_object"
            }, model="openai/gpt-4.1")
            print(response, flush=True)
            try:
                response_json = json.loads(response)
                messages.append({"role": "assistant", "content": [{"type": "text", "text": response}]})
            except json.JSONDecodeError:
                print("Invalid JSON response", flush=True)
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
                    messages.append({"role": "assistant", "content": [{"type": "text", "text": json.dumps(tool_result)}]})
                    print(tool_result, flush=True)

                    if tool_call["name"] == "talk_to_user":
                        terminate = True
                        break
            if terminate:
                break

if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else None
    main(project_dir)