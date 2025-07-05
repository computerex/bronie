import subprocess
from tools.talk_to_user import talk_to_user

def exec_shell(command):
    """
    Execute a shell command and return the results.
    Runs commands in the current working directory (project directory).
    Captures both stdout and stderr, and provides formatted output.
    
    Args:
        command (str): The shell command to execute (e.g., "ls -la", "git status")
        
    Returns:
        dict: Dictionary containing:
            - stdout (str): Standard output from command (with trailing whitespace stripped)
            - stderr (str): Standard error from command (with trailing whitespace stripped)
            - formatted_output (str): Combined stdout and stderr output (with whitespace stripped)
    """
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Strip whitespace but preserve line structure
    stdout = result.stdout.rstrip()
    stderr = result.stderr.rstrip()
    combined = f"{stdout}\n{stderr}".strip()
    
    return {
        'stdout': stdout,
        'stderr': stderr,
        'formatted_output': combined
    }
