from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def talk_to_user(message):
    """
    Communicate with the user by returning a message.
    
    Args:
        message (str): Message to send to the user
        
    Returns:
        str: The message to display to the user
    """
    return message

if __name__ == "__main__":
    console = Console()
    msg = talk_to_user("Hello World!")
    # For testing, we'll show it in a panel
    console.print(Panel(msg))
