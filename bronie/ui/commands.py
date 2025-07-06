from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from ..tools.exec_shell import exec_shell
from ..tools.clipboard_image import get_clipboard_image, is_image_in_clipboard
from ..tools.config import (
    set_agent_model, set_code_model, set_light_model,
    get_agent_model, get_code_model, get_light_model
)
from .. import token_tracker
# Avoid importing llm at module level to prevent circular dependencies.
# We'll import list_openrouter_models lazily within handle_list_models_command when needed.

console = Console()

def handle_exec_command(line_stripped, context):
    """Handle :e command - execute shell command directly"""
    command = line_stripped[3:].strip()  # Extract everything after ':e '
    result = exec_shell(command)
    if isinstance(result, dict) and "formatted_output" in result:
        console.print(Panel(result["formatted_output"], title="Shell Output", highlight=True))
    else:
        console.print(Panel(str(result), title="Shell Output", highlight=True))
    return True

def handle_mode_toggle(context):
    """Handle :m command - toggle input mode"""
    context["multiline_mode"][0] = not context["multiline_mode"][0]
    mode_name = "multiline" if context["multiline_mode"][0] else "single-line"
    console.print(f"[green]Switched to {mode_name} mode[/]")
    return True

def handle_clear_command(context):
    """Handle :clear command - reset message history and token counts"""
    # Clear the *existing* messages list in-place so any references held
    # elsewhere (e.g. Agent.self.messages) are updated too.
    msgs = context["messages"]
    msgs.clear()
    msgs.append(context["get_agent_system_prompt"]())
    context["attached_images"] = []

    console.print("[green]Message history cleared (session token totals preserved)[/]")
    return True

def handle_image_command(context):
    """Handle :image command - paste image from clipboard"""
    if is_image_in_clipboard():
        base64_data, mime_type = get_clipboard_image()
        if base64_data:
            context["attached_images"].append(base64_data)
            console.print(Text("📸 Image from clipboard attached", style="green"))
        else:
            console.print(Text("❌ Failed to get image from clipboard", style="red"))
    else:
        console.print(Text("❌ No image found in clipboard", style="red"))
    return True

def handle_drop_command(context):
    """Handle :drop command - remove the last attached image"""
    if context["attached_images"]:
        context["attached_images"].pop()
        console.print(Text("🗑️ Last image removed", style="yellow"))
    else:
        console.print(Text("❌ No images to remove", style="red"))
    return True

def handle_compress_command(context, n=10):
    """Handle :compress command - compress older messages based on recent context."""
    # Import here to avoid circular dependencies
    from ..llm import complete_chat
    import json

    messages = context["messages"]
    
    # We need a system prompt, something to compress, and recent context.
    # So at least n + 2 messages to be meaningful.
    if len(messages) < n + 2:
        console.print(f"[yellow]Not enough messages to perform a meaningful compression. Need at least {n+2} messages.[/yellow]")
        return True

    console.print(f"[yellow]Analyzing recent conversation and compressing older history...[/]")

    system_prompt = messages[0]
    history = messages[1:]
    
    # The last N messages are the recent context, which we will NOT compress.
    recent_messages = history[-n:]
    # The messages before that are the ones we will compress.
    messages_to_compress = history[:-n]

    if not messages_to_compress:
        console.print("[yellow]No older messages to compress.[/yellow]")
        return True

    def format_messages_for_prompt(msgs):
        """Helper to format a list of message objects into a string."""
        formatted = []
        for msg in msgs:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            text_content = ""
            if isinstance(content, list):
                # Handle complex content like images
                for part in content:
                    if part.get("type") == "text":
                        text_content += part.get("text", "") + "\n"
            else:
                text_content = str(content)
            
            # For JSON tool calls, pretty print for clarity
            # The text_content is a stringified JSON, so we check for a keyword
            if '"tool_calls"' in text_content:
                try:
                    # Attempt to load and format it as pretty json
                    json_content = json.loads(text_content)
                    text_content = json.dumps(json_content, indent=2)
                except json.JSONDecodeError:
                    pass # Keep as-is if not valid json

            formatted.append(f"<{role}>\n{text_content.strip()}\n</{role}>")
        return "\n---\n".join(formatted)

    recent_context_str = format_messages_for_prompt(recent_messages)
    to_compress_str = format_messages_for_prompt(messages_to_compress)

    compression_prompt = f"""
Your task is to act as a memory compression module for a software engineering AI agent.
You will be given the most RECENT part of a conversation to understand the agent's current task.
Then, you will be given the OLDER part of the conversation.
You must compress the OLDER part into a concise summary, preserving all information *that is relevant to the RECENT conversation*.

Key information to preserve from the OLDER conversation includes:
- Previously discussed file paths, filenames, and code snippets that are related to the current task.
- Key decisions, requirements, or constraints that were established earlier.
- Important context or background information that the agent might need to remember.

Eliminate conversational filler, redundant interactions, and information that is no longer relevant to the agent's current focus, as defined by the RECENT conversation.
The output should be a single block of text that is a coherent summary of the compressed history.

**RECENT CONVERSATION (Your guide for what's important):**
---
{recent_context_str}
---

**OLDER CONVERSATION HISTORY (Compress this part):**
---
{to_compress_str}
---

Now, provide the compressed summary of the OLDER conversation history. Output *only* the summary text, without any introductory phrases.
"""

    try:
        compressed_content = complete_chat(
            messages=[{"role": "user", "content": compression_prompt}],
            model=get_light_model()
        )

        # Create the new summary message to insert
        summary_message = {
            "role": "system", 
            "content": f"The preceding conversation has been summarized to save tokens. Key details relevant to the current task were preserved:\n\n{compressed_content}"
        }

        # Reconstruct the final message list
        new_messages = []
        new_messages.append(system_prompt)
        new_messages.append(summary_message)
        new_messages.extend(recent_messages) # Add the uncompressed recent messages back

        # Replace the original messages in the main message list *in-place*
        original_len = len(messages)
        messages.clear()
        messages.extend(new_messages)
        new_len = len(messages)

        console.print(Panel(
            f"[bold]Compression complete.[/bold]\n"
            f"Original message count: {original_len}\n"
            f"New message count: {new_len}\n"
            f"Compressed {len(messages_to_compress)} message(s) into 1 summary.",
            title="Context Compressed",
            border_style="yellow"
        ))

    except Exception as e:
        console.print(Text(f"An error occurred during compression: {e}", style="red"))

    return True

def handle_set_agent_model_command(line_stripped, context):
    """Handle :set-agent-model command - set the agent model"""
    if line_stripped.startswith(":set-agent-model "):
        model = line_stripped[17:].strip()  # Extract everything after ':set-agent-model '
        if model:
            set_agent_model(model)
            console.print(Text(f"✅ Agent model set to: {model}", style="green"))
        else:
            console.print(Text("❌ Please provide a model name", style="red"))
        return True
    return False

def handle_set_code_model_command(line_stripped, context):
    """Handle :set-code-model command - set the code editing model"""
    if line_stripped.startswith(":set-code-model "):
        model = line_stripped[16:].strip()  # Extract everything after ':set-code-model '
        if model:
            set_code_model(model)
            console.print(Text(f"✅ Code model set to: {model}", style="green"))
        else:
            console.print(Text("❌ Please provide a model name", style="red"))
        return True
    return False

def handle_set_light_model_command(line_stripped, context):
    """Handle :set-light-model command - set the light utility model"""
    if line_stripped.startswith(":set-light-model "):
        model = line_stripped[17:].strip()
        if model:
            set_light_model(model)
            console.print(Text(f"✅ Light model set to: {model}", style="green"))
        else:
            console.print(Text("❌ Please provide a model name", style="red"))
        return True
    return False

def handle_show_models_command(line_stripped, context):
    """Handle :models command - show current model settings"""
    if line_stripped == ":models":
        current_agent = get_agent_model()
        current_code = get_code_model()
        current_light = get_light_model()
        console.print(Panel(
            f"[bold]Current Model Settings:[/bold]\n"
            f"🤖 Agent Model: [cyan]{current_agent}[/cyan]\n"
            f"💻 Code Model:  [cyan]{current_code}[/cyan]\n"
            f"💡 Light Model: [cyan]{current_light}[/cyan]\n\n"
            f"[dim]Use :set-agent-model <model>, :set-code-model <model>, or :set-light-model <model> to change[/dim]\n"
            f"[dim]Use :list-models to see available models[/dim]",
            title="Model Configuration",
            border_style="blue"
        ))
        return True
    return False

def handle_list_models_command(line_stripped, context):
    """Handle :list-models command - show available models"""
    if line_stripped == ":list-models":
        # Import here to avoid circular import issues during application startup
        from ..llm import list_models
        try:
            models = list_models()
            
            # Create a table to display models
            table = Table(title="Available Models")
            table.add_column("Model ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Provider", style="yellow")
            table.add_column("Context Length", style="magenta")
            
            # Sort models by name for better readability
            sorted_models = sorted(models, key=lambda x: x.get('name', ''))
            
            for model in sorted_models:
                model_id = model.get('id', 'N/A')
                name = model.get('name', 'N/A')
                provider = model.get('provider', {}).get('name', 'N/A')
                context_length = model.get('context_length', 'N/A')
                
                table.add_row(model_id, name, provider, str(context_length))
            
            console.print(table)
            console.print(Panel(
                "[dim]Use :set-agent-model <model_id> or :set-code-model <model_id> to change models[/dim]",
                title="Usage",
                border_style="blue"
            ))
            
        except Exception as e:
            console.print(Text(f"❌ Error fetching models: {e}", style="red"))
        
        return True
    return False

def handle_ui_command(line, context):
    """Handle UI commands - exactly the same behavior as current code"""
    line_stripped = line.strip()
    
    if line_stripped.startswith(":e "):
        return handle_exec_command(line_stripped, context)
    elif line_stripped == ":m":
        return handle_mode_toggle(context)
    elif line_stripped == ":clear":
        return handle_clear_command(context)
    elif line_stripped == ":compress":
        return handle_compress_command(context)
    elif line_stripped == ":image":
        return handle_image_command(context)
    elif line_stripped == ":drop":
        return handle_drop_command(context)
    elif line_stripped == ":models":
        return handle_show_models_command(line_stripped, context)
    elif line_stripped == ":list-models":
        return handle_list_models_command(line_stripped, context)
    elif line_stripped.startswith(":set-agent-model "):
        return handle_set_agent_model_command(line_stripped, context)
    elif line_stripped.startswith(":set-code-model "):
        return handle_set_code_model_command(line_stripped, context)
    elif line_stripped.startswith(":set-light-model "):
        return handle_set_light_model_command(line_stripped, context)
    
    return None  # Not a UI command 
