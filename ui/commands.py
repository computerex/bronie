from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from tools.exec_shell import exec_shell
from tools.clipboard_image import get_clipboard_image, is_image_in_clipboard
from tools.config import set_agent_model, set_code_model, get_agent_model, get_code_model
from llm import list_openrouter_models
import token_state

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
    token_state.reset_token_counts()  # Reset token counts
    console.print("[green]Message history and token counts cleared[/]")
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

def handle_show_models_command(line_stripped, context):
    """Handle :models command - show current model settings"""
    if line_stripped == ":models":
        current_agent = get_agent_model()
        current_code = get_code_model()
        console.print(Panel(
            f"[bold]Current Model Settings:[/bold]\n"
            f"🤖 Agent Model: [cyan]{current_agent}[/cyan]\n"
            f"💻 Code Model: [cyan]{current_code}[/cyan]\n\n"
            f"[dim]Use :set-agent-model <model> or :set-code-model <model> to change[/dim]\n"
            f"[dim]Use :list-models to see available OpenRouter models[/dim]",
            title="Model Configuration",
            border_style="blue"
        ))
        return True
    return False

def handle_list_models_command(line_stripped, context):
    """Handle :list-models command - show available OpenRouter models"""
    if line_stripped == ":list-models":
        try:
            models = list_openrouter_models()
            
            # Create a table to display models
            table = Table(title="Available OpenRouter Models")
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
    
    return None  # Not a UI command 
