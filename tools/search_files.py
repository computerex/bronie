import os
import re
from pathlib import Path

def search_files(pattern, directory='.'):
    """
    Search for files by regex patterns.
    
    Args:
        pattern (str): Regex pattern to match against file names
        directory (str, optional): Directory to search in. Defaults to current directory.
        
    Returns:
        str: Formatted list of matching files
    """
    try:
        # Compile the regex pattern
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Invalid regex pattern: {e}"
        
        # Ensure the path is relative to the current working directory
        # which should be the project directory set in main.py
        directory = os.path.join(os.getcwd(), directory)
            
        # Get the absolute path of the directory
        abs_path = os.path.abspath(directory)
        
        if not os.path.exists(abs_path):
            return f"Directory not found: {directory}"
            
        if not os.path.isdir(abs_path):
            return f"Not a directory: {directory}"
            
        # Find all matching files
        matches = []
        
        for root, dirs, files in os.walk(abs_path):
            # Skip hidden directories (starting with .)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if regex.search(file):
                    rel_path = os.path.relpath(os.path.join(root, file), abs_path)
                    matches.append(rel_path)
                    
        # Sort matches
        matches.sort()
        
        # Format the output
        if matches:
            result = [f"Files matching pattern '{pattern}' in {abs_path}:"]
            for i, match in enumerate(matches, 1):
                result.append(f"{i:3d}. {match}")
            return "\n".join(result)
        else:
            return f"No files matching pattern '{pattern}' found in {abs_path}."
            
    except Exception as e:
        return f"Error searching files: {e}"
