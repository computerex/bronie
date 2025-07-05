import time
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.validation import Validator, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from ui.commands import handle_ui_command
import token_state

console = Console()

# Global last-interrupt timestamp for double Ctrl+C detection
# (Placed before other imports so linters group it with stdlib)
_last_interrupt_time = 0.0

def get_user_input(multiline_mode, attached_images, get_agent_system_prompt, messages):
    """Enhanced user input processing with prompt_toolkit multiline support"""
    global _last_interrupt_time
    
    token_count = count_tokens(messages)
    
    session_input = token_state.input_tokens
    session_output = token_state.output_tokens
    session_total = session_input + session_output
    console.print(f"[cyan]Token count:[/] {token_count} | [yellow]Session:[/] {session_input:,} in, {session_output:,} out, {session_total:,} total")
    
    mode_text = "[green]Multiline[/]" if multiline_mode[0] else "[blue]Single-line[/]"
    
    # Show attached images if any
    if attached_images:
        console.print(f"[magenta]Attached images:[/] {len(attached_images)}")
    
    console.print(Panel(
        "[bold]Enter your message below[/]\n"
        f"Current mode: {mode_text}\n"
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
        "- [bold]:end[/bold] on a new line when finished in multiline mode",
        title="Input Instructions",
        border_style="green"
    ))
    
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
        prompt_continuation=lambda width, line_number, wrap_count: '.' * width
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
    
    except KeyboardInterrupt:
        current_time = time.time()
        # Second interrupt within 1 second? -> exit.
        if current_time - _last_interrupt_time < 1:
            console.print("\n[red]Double interrupt detected - exiting[/]")
            sys.exit(0)
        # First interrupt: save timestamp and inform user.
        _last_interrupt_time = current_time
        console.print("\n[yellow]Press Ctrl+C again within 1 second to exit[/]")
        return None, False

def count_tokens(messages):
    """Count tokens in messages - moved from main.py"""
    import tiktoken
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
