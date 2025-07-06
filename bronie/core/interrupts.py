import sys
import time
from rich.console import Console

_last_interrupt_time = 0.0

def handle_keyboard_interrupt(console: Console):
    """Unified Ctrl+C handler – exits on double-tap within 1 s."""
    global _last_interrupt_time
    current_time = time.time()
    if current_time - _last_interrupt_time < 1:
        console.print("\n[red]Double Ctrl+C detected - exiting[/]")
        sys.exit(0)
    _last_interrupt_time = current_time
    console.print("\n[yellow]Press Ctrl+C again within 1 second to exit[/]") 