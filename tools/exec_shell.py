import subprocess
from tools.talk_to_user import talk_to_user

def exec_shell(command):
    """
    Execute a shell command after getting user approval.
    
    Args:
        command (str): The shell command to execute
        
    Returns:
        dict: Dictionary containing:
            - stdout (str): Standard output from command
            - stderr (str): Standard error from command 
            - formatted_output (str): Combined output with whitespace stripped
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
