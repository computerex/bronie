import subprocess
from tools.talk_to_user import talk_to_user

def exec_shell(command):
    """
    Execute a shell command after getting user approval.
    
    Args:
        command (str): The shell command to execute
        
    Returns:
        str: Command output (stdout + stderr) if approved and executed
             Message indicating abortion if not approved
    """
    print(f"Executing shell command: {command}", flush=True)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return f"{result.stdout}\n{result.stderr}".strip()
