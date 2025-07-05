import time
import sys
from prompt_toolkit import prompt
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from ui.commands import handle_ui_command
import token_state

console = Console()

def get_user_input(multiline_mode, attached_images, get_agent_system_prompt, messages):
    """Handle user input processing - exactly the same behavior as current code"""
    last_interrupt_time = 0
    
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
    
    lines = []
    mode_switched = False
    while True:
        try:
            # Use simple prompt for each line
            line = prompt('')
            
            # Create context for UI commands
            context = {
                "multiline_mode": multiline_mode,
                "attached_images": attached_images,
                "get_agent_system_prompt": get_agent_system_prompt,
                "messages": messages
            }
            
            # Handle UI commands
            ui_result = handle_ui_command(line, context)
            if ui_result:
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
        return None, True  # Skip processing when just toggling modes

    if not lines:  # Handle empty input
        console.print("[yellow]Empty input, please try again[/]")
        return None, False
    
    user_input = "\n".join(lines)
    return user_input, False

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