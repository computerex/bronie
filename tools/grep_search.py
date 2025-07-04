import os
import re
import subprocess
from pathlib import Path

def grep_search(pattern, file_pattern="*"):
    """
    Search for patterns in files using grep or a Python-based alternative.
    
    Args:
        pattern (str): The pattern to search for
        file_pattern (str, optional): File pattern to search in. Defaults to "*".
        
    Returns:
        str: Results of the search
    """
    try:
        # Get current working directory (project directory)
        project_dir = os.getcwd()
        
        # Try to use grep if available (Unix/Linux/Mac)
        if os.name != 'nt':  # Not Windows
            try:
                cmd = ["grep", "-r", "--include", file_pattern, pattern, "."]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode in [0, 1]:  # grep returns 1 if no matches found
                    return result.stdout if result.stdout else "No matches found."
                else:
                    # Fall back to Python implementation if grep fails
                    raise subprocess.SubprocessError("grep command failed")
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fall back to Python implementation
                pass
                
        # Python-based implementation (for Windows or if grep fails)
        results = []
        cwd = Path(project_dir)
        
        for path in cwd.rglob(file_pattern):
            if path.is_file():
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                # Convert path to be relative to project directory
                                rel_path = path.relative_to(cwd)
                                results.append(f"{rel_path}:{i}: {line.rstrip()}")
                except Exception as e:
                    # Convert path to be relative to project directory
                    rel_path = path.relative_to(cwd)
                    results.append(f"Error reading {rel_path}: {e}")
                    
        if results:
            return "\n".join(results)
        else:
            return "No matches found."
            
    except Exception as e:
        return f"Error during grep search: {e}"
