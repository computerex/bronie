from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def talk_to_user(message):
    """
    Communicate with the user by returning a message in a panel format.
    This tool cedes control back to the user and should be the last tool in a chain.
    Useful for providing final results, asking for user input, or displaying important information.
    
    Args:
        message (str): Message to send to the user (supports markdown formatting)
        
    Returns:
        dict: Dictionary containing:
            - type: Always 'panel'
            - content: The message content to display
    """
    return {'type': 'panel', 'content': message}

if __name__ == "__main__":
    console = Console()
    msg = talk_to_user("Hello World!")
    # For testing, we'll show it in a panel
    console.print(Panel(msg))
