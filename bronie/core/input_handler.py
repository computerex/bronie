import sys
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from ..ui.commands import handle_ui_command
from .interrupts import handle_keyboard_interrupt
import tiktoken
from .. import token_tracker

console = Console()

def get_input_instructions_panel(mode_text, project_dir):
    return Panel(
        "[bold]Enter your message below[/]\n"
        f"Current mode: {mode_text}\n"
        f"Project directory: {os.path.abspath(project_dir) if project_dir else os.path.abspath(os.getcwd())}\n"
        "[dim]Available commands:\n"
        "- [bold]:m[/bold] to toggle input mode\n"
        "- [bold]:clear[/bold] to reset message history\n"
        "- [bold]:e <shell command>[/bold] to execute a shell command directly\n"
        "- [bold]:image[/bold] to paste image from clipboard\n"
        "- [bold]:drop[/bold] to remove the last attached image\n"
        "- [bold]:models[/bold] to show current model settings\n"
        "- [bold]:list-models[/bold] to see available OpenRouter models\n"
        "- [bold]:set-agent-model <model>[/bold] to change agent model\n"
        "- [bold]:set-code-model <model>[/bold] to change code editing model\n"
        "- [bold]:set-light-model <model>[/bold] to change light utility model\n"
        "- [bold]:end[/bold] on a new line when finished in multiline mode",
        title="Input Instructions",
        border_style="green"
    )

# Cache encoder once for efficiency
ENCODER = tiktoken.encoding_for_model("gpt-4")

def get_user_input(multiline_mode, attached_images, get_agent_system_prompt, messages, project_dir=None):
    """Enhanced user input processing with prompt_toolkit multiline support"""
    
    token_count = count_tokens(messages)
    
    # Aggregate session token usage (input/output)
    in_tokens, out_tokens = token_tracker.get_totals()
    total_tokens = in_tokens + out_tokens

    console.print(
        f"[cyan]Context tokens:[/] {token_count:,} "
        f"[dim]| Session in/out:[/] {in_tokens:,}/{out_tokens:,} "
        f"(total {total_tokens:,})"
    )
    
    mode_text = "[green]Multiline[/]" if multiline_mode[0] else "[blue]Single-line[/]"
    
    # Show attached images if any
    if attached_images:
        console.print(f"[magenta]Attached images:[/] {len(attached_images)}")
    
    console.print(get_input_instructions_panel(mode_text, project_dir))
    
    # -------------------------------------------------------------------
    # Key bindings
    # In multiline mode, pressing <Enter> on a line that consists solely
    # of ":end" should immediately accept the entire buffer. We create a
    # small, local KeyBindings object for this behaviour and only attach
    # it when multiline mode is active, leaving single-line behaviour
    # untouched.
    # -------------------------------------------------------------------
    kb = None
    if multiline_mode[0]:
        kb = KeyBindings()

        @kb.add("enter")
        def _(event):
            """Custom <Enter> behaviour for multiline mode."""
            buf = event.app.current_buffer
            doc = buf.document
            # If the current line is just ':end', accept the buffer.
            if doc.current_line.strip() == ":end":
                # Remove the ':end' line before accepting.
                buf.delete_before_cursor(len(doc.current_line))
                # Accept the buffer and return the text.
                event.app.exit(result=buf.text.rstrip("\n"))
            else:
                # Default action: insert a newline.
                buf.insert_text("\n")

    # Session setup with the (optional) custom key bindings
    session = PromptSession(
        multiline=multiline_mode[0],
        complete_while_typing=False,
        validate_while_typing=False,
        key_bindings=kb,
        prompt_continuation=lambda width, line_number, _: '.' * width
    )
    
    try:
        context = {
            "multiline_mode": multiline_mode,
            "attached_images": attached_images,
            "get_agent_system_prompt": get_agent_system_prompt,
            "messages": messages
        }
        
        # Get user input
        user_input = session.prompt(
            HTML('<ansired>➤</ansired> '),
            style=Style.from_dict({
                '': '#ansigreen',
            })
        )

        # --------------------------------------------------------------
        # Multiline handling: detect the special ":end" marker
        # When the session is in multiline mode, users can finish their
        # message by typing ":end" on a new line. Prompt-toolkit will
        # return the full buffer including that marker. We strip the
        # marker **and everything on that final line** so that the agent
        # receives only the actual message content.
        # --------------------------------------------------------------
        if multiline_mode[0]:
            stripped_input = user_input.rstrip("\n")  # remove trailing newlines for inspection
            lines = stripped_input.splitlines()
            if lines and lines[-1].strip() == ":end":
                # Remove the last line (":end") and rebuild the input
                lines = lines[:-1]
                user_input = "\n".join(lines).rstrip()

        # Process UI commands first, before any other checks
        ui_result = handle_ui_command(user_input, context)
        if ui_result:
            return None, True

        # After removing ':end', a completely empty buffer means the user
        # pressed enter without any actual content. In that case, prompt
        # them again rather than sending an empty message.
        if not user_input.strip():
            console.print("[yellow]Empty input, please try again[/]")
            return None, False
        
        return user_input, False
    
    except EOFError:
        # Ctrl+D at the prompt: just treat as empty input (ignore)
        console.print("[yellow]Ctrl+D pressed (no active model) – nothing to cancel[/]")
        return None, False
    except KeyboardInterrupt:
        handle_keyboard_interrupt(console)
        return None, False

def count_tokens(messages):
    """Count tokens in messages - moved from main.py"""
    num_tokens = 0
    for message in messages:
        if isinstance(message["content"], str):
            num_tokens += len(ENCODER.encode(message["content"]))
        elif isinstance(message["content"], list):
            for content in message["content"]:
                if isinstance(content, dict) and "text" in content:
                    num_tokens += len(ENCODER.encode(content["text"]))
    return num_tokens 
