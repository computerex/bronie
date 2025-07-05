import json
import sys
import os
import re
from rich.console import Console
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.panel import Panel
from rich.text import Text
from llm import complete_chat, complete_chat_stream, get_agent_model
from tools.registry import dispatch_tool
from core.input_handler import get_user_input
from core.interrupts import handle_keyboard_interrupt

console = Console()

# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------

# A tolerant JSON parser for model responses that may contain
# markdown fences, extra logging text, or minor formatting issues.
def robust_json_parse(text: str):
    """Attempt to load JSON from *text* while handling common issues.

    1. Strips markdown code fences (``` or ```json).
    2. Falls back to the substring between the first "{" and the last "}".
    3. Removes trailing commas that would invalidate JSON.

    Returns the parsed object on success, otherwise ``None``.
    """
    stripped = text.strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # find the first { and the last }
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    FIX_PROMPT = """You need to fix this JSON object. Please fix it such that it cleanly decodes. Output only the fixed JSON object, no other text."""
    json_fixed = complete_chat(messages=[
        {"role": "system", "content": FIX_PROMPT},
        {"role": "user", "content": stripped}
    ], model="gpt-4.1-mini", response_format={"type": "json_object"})
    print('Fixing model JSON...')
    return json.loads(json_fixed)

class Agent:
    def __init__(self, project_dir=None, get_agent_system_prompt=None):
        self.project_dir = project_dir
        self.get_agent_system_prompt = get_agent_system_prompt
        self.multiline_mode = [False]
        self.attached_images = []
        self.messages = [get_agent_system_prompt()] if get_agent_system_prompt else []
    
    def run(self):
        """Main conversation loop - exactly the same behavior as current main()"""
        while True:
            try:
                # Get user input
                user_input, mode_switched = get_user_input(
                    self.multiline_mode, 
                    self.attached_images, 
                    self.get_agent_system_prompt, 
                    self.messages,
                    self.project_dir
                )
                
                if mode_switched:
                    continue  # Skip processing when just toggling modes

                if user_input is None:
                    continue  # Handle empty input
                
                # Create message content with text and images
                message_content = []
                message_content.append({"type": "text", "text": user_input})
                
                # Add images to the message content if any
                for img_base64 in self.attached_images:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                    })
                
                # Add message with text and images
                if self.attached_images:
                    self.messages.append({"role": "user", "content": message_content})
                    console.print(Text("📤 Message sent with attached images", style="green"))
                else:
                    self.messages.append({"role": "user", "content": user_input})
                
                # Clear attached images after sending
                current_images = self.attached_images.copy()  # Make a copy for use in this iteration
                self.attached_images = []
                
                terminate = False
                # Get the user-selected agent model
                agent_model = get_agent_model()
                
                while True:
                    # Try streaming first for better user experience, fall back to regular completion if needed
                    try:
                        response = ""
                        for chunk in complete_chat_stream(messages=self.messages, response_format={
                            "type": "json_object"
                        }, model=agent_model):
                            if chunk:
                                sys.stdout.write(chunk)
                                sys.stdout.flush()
                                response += chunk
                                # Note: Ctrl+D detection removed as it's not compatible with Windows
                                # Users can use Ctrl+C to interrupt instead
                        print()  # New line after streaming completes
                    except KeyboardInterrupt:
                        handle_keyboard_interrupt(console)
                        break  # Return control to input prompt after first Ctrl+C
                    except EOFError:
                        console.print("\n[yellow]Model response interrupted - returning to input[/]")
                        break  # Break out to input
                    except Exception as e:
                        console.print(f"[yellow]Streaming failed, falling back to regular completion: {e}[/]")
                        try:
                            response = complete_chat(messages=self.messages, response_format={
                                "type": "json_object"
                            }, model=agent_model)
                            console.print(Markdown(response))
                        except KeyboardInterrupt:
                            handle_keyboard_interrupt(console)
                            break  # Return control to input prompt after second Ctrl+C
                    
                    # ----------------------------------------------------
                    # Robust JSON parsing of the model response
                    # ----------------------------------------------------
                    response_json = robust_json_parse(response)
                    if response_json is None:
                        console.print("[bold red]Invalid JSON response[/]")
                        break  # Don't exit, just break and return to input

                    # Record the *raw* response text in the conversation context
                    self.messages.append({"role": "assistant", "content": [{"type": "text", "text": response}]})

                    if "tool_calls" in response_json:
                        for tool_call in response_json["tool_calls"]:
                            try:
                                # Handle special case for edit_file with images
                                if tool_call["name"] == "edit_file" and current_images:
                                    tool_result = dispatch_tool(
                                        tool_call["name"], 
                                        target_file=tool_call["parameters"]["target_file"],
                                        instructions=tool_call["parameters"]["instructions"],
                                        images=current_images
                                    )
                                else:
                                    # Use the tool registry instead of if-else chain
                                    tool_result = dispatch_tool(tool_call["name"], **tool_call["parameters"])
                                
                                # Record the tool result in the conversation so the model can see it
                                self.messages.append({"role": "user", "content": [{"type": "text", "text": json.dumps(tool_result)}]})

                                # If tool_result signals an error, explicitly add a readable message for the model
                                if isinstance(tool_result, dict) and "error" in tool_result:
                                    error_note = f"Tool call '{tool_call['name']}' failed: {tool_result['error']}"
                                    self.messages.append({"role": "user", "content": error_note})
                                    console.print(Text(error_note, style="yellow"))

                                if tool_call["name"] == "talk_to_user":
                                    if isinstance(tool_result, dict) and "type" in tool_result and "content" in tool_result:
                                        if tool_result["type"] == "markdown":
                                            console.print(Markdown(tool_result["content"]))
                                        elif tool_result["type"] == "panel":
                                            console.print(Panel(tool_result["content"]))
                                    terminate = True
                                    break
                                elif isinstance(tool_result, dict) and "formatted_output" in tool_result:
                                    console.print(Panel(tool_result["formatted_output"], title="Shell Output", highlight=True))
                                elif isinstance(tool_result, str):
                                    console.print(Markdown(tool_result))
                                else:
                                    console.print(Pretty(tool_result))
                            except KeyboardInterrupt:
                                handle_keyboard_interrupt(console)
                                break  # Return control to input prompt after Ctrl+C
                            except Exception as e:
                                # Catch-all for unexpected tool errors and inform both console and conversation
                                err_msg = f"Tool call '{tool_call['name']}' raised an exception: {e}"
                                console.print(Text(err_msg, style="red"))
                                self.messages.append({"role": "user", "content": err_msg})

                    else: # no tool calls
                        self.messages.append({"role": "user", "content": "Please respond strictly in the JSON format specified in the system prompt."})
                        console.print("Please respond strictly in the JSON format specified in the system prompt: {\"tool_calls\": [...]}")
                        continue
                    if terminate:
                        break

            except KeyboardInterrupt:
                handle_keyboard_interrupt(console)
                continue  # Return to top of main loop
