import json
import sys
import select
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.panel import Panel
from rich.text import Text
from llm import complete_chat, complete_chat_stream, get_agent_model
from tools.registry import dispatch_tool
from core.input_handler import get_user_input

console = Console()

# Global timestamp for double Ctrl+C detection
_last_interrupt_time = 0.0

def _handle_keyboard_interrupt():
    """Handle Ctrl+C; exit if pressed twice within 1 second."""
    global _last_interrupt_time
    current_time = time.time()
    if current_time - _last_interrupt_time < 1:
        console.print("\n[red]Double Ctrl+C detected - exiting[/]")
        sys.exit(0)
    _last_interrupt_time = current_time
    console.print("\n[yellow]Press Ctrl+C again within 1 second to exit[/]")

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
                    self.messages
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
                                # Detect Ctrl+D (EOF) to abort streaming
                                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                                    data = sys.stdin.read(1)
                                    if data == '' or data == '\x04':
                                        raise EOFError
                        print()  # New line after streaming completes
                    except KeyboardInterrupt:
                        _handle_keyboard_interrupt()
                        break  # Return control to input prompt after first Ctrl+C
                    except EOFError:
                        console.print("\n[yellow]Model response interrupted by Ctrl+D - returning to input[/]")
                        break  # Break out to input
                    except Exception as e:
                        console.print("[yellow]Streaming failed, falling back to regular completion[/]")
                        try:
                            response = complete_chat(messages=self.messages, response_format={
                                "type": "json_object"
                            }, model=agent_model)
                            console.print(Markdown(response))
                        except KeyboardInterrupt:
                            _handle_keyboard_interrupt()
                            break  # Return control to input prompt after second Ctrl+C
                    
                    try:
                        if response.startswith("```json"):
                            response = response[7:-3]
                        if response.startswith("```"):
                            response = response[3:-3]
                        if response.endswith("```"):
                            response = response[:-3]
                        response_json = json.loads(response)
                        self.messages.append({"role": "assistant", "content": [{"type": "text", "text": response}]})
                    except json.JSONDecodeError:
                        console.print("[bold red]Invalid JSON response[/]")
                        break  # Don't exit, just break and return to input

                    if "tool_calls" in response_json:
                        for tool_call in response_json["tool_calls"]:
                            try:
                                # Handle special case for edit_file with images
                                if tool_call["name"] == "edit_file" and current_images:
                                    tool_result = dispatch_tool(
                                        tool_call["name"], 
                                        filename=tool_call["parameters"]["filename"],
                                        editing_instructions=tool_call["parameters"]["editing_instructions"],
                                        images=current_images
                                    )
                                else:
                                    # Use the tool registry instead of if-else chain
                                    tool_result = dispatch_tool(tool_call["name"], **tool_call["parameters"])
                                
                                self.messages.append({"role": "assistant", "content": [{"type": "text", "text": json.dumps(tool_result)}]})
                                
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
                                _handle_keyboard_interrupt()
                                break  # Return control to input prompt after Ctrl+C

                    if terminate:
                        break

            except KeyboardInterrupt:
                _handle_keyboard_interrupt()
                continue  # Return to top of main loop
