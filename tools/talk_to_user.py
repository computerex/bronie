from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def talk_to_user(message):
    """
    Communicate with the user by returning message in a panel format. Cedes control back to the user.
    Should be the last tool in the chain since it will return control to the user.
    
    Args:
        message (str): Message to send to the user
        
    Returns:
        dict: Dictionary containing message type ('panel') and content
    """
    return {'type': 'panel', 'content': message}

if __name__ == "__main__":
    console = Console()
    msg = talk_to_user("Hello World!")
    # For testing, we'll show it in a panel
    console.print(Panel(msg))
