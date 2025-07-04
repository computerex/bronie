from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def talk_to_user(message):
    """
    Communicate with the user by returning message with type information.
    
    Args:
        message (str): Message to send to the user
        
    Returns:
        dict: Dictionary containing message type ('markdown' or 'panel') and content
    """
    # Check if message contains markdown-like content
    markdown_indicators = ['#', '*', '_', '`', '>', '-', '[', ']']
    is_markdown = any(indicator in message for indicator in markdown_indicators)
    
    if is_markdown:
        return {'type': 'markdown', 'content': message}
    else:
        return {'type': 'panel', 'content': message}

if __name__ == "__main__":
    console = Console()
    msg = talk_to_user("Hello World!")
    # For testing, we'll show it in a panel
    console.print(Panel(msg))
