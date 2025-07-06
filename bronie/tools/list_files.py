import os
from pathlib import Path
from .config import IGNORED_DIRS

def count_lines(file_path):
    """
    Count the number of lines in a file.
    
    Args:
        file_path (str or Path): Path to the file
        
    Returns:
        int: Number of lines in the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def list_files(directory_path='.'):
    """
    List files and directories in a specified path with detailed information.
    Provides file sizes, line counts, and type information.
    Automatically ignores common dependency directories (node_modules, .git, etc.).
    
    Args:
        directory_path (str, optional): Relative path to the directory to list (from project directory). Defaults to current directory.
        
    Returns:
        dict: Dictionary containing:
            - path: Absolute path of the directory listed
            - entries: List of dicts containing:
                - name: File or directory name
                - type: 'file' or 'directory'
                - size: File size in bytes (0 for directories)
                - lines: Number of lines in file (0 for directories)
            - error: Error message if operation fails
    """
    try:
        # Convert to absolute path if relative
        # Ensure the path is relative to the current working directory
        # which should be the project directory set in main.py
        directory_path = os.path.join(os.getcwd(), directory_path)
        abs_path = os.path.abspath(directory_path)
        
        if not os.path.exists(abs_path):
            return f"Directory not found: {directory_path}"
            
        if not os.path.isdir(abs_path):
            return f"Not a directory: {directory_path}"
            
        # Get all files and directories in the specified path
        entries = []
        
        for entry in os.scandir(abs_path):
            # Skip ignored directories
            if entry.is_dir() and entry.name in IGNORED_DIRS:
                continue
                
            if entry.is_file():
                line_count = count_lines(entry.path)
                size = entry.stat().st_size
                entries.append({
                    'name': entry.name,
                    'type': 'file',
                    'size': size,
                    'lines': line_count
                })
            elif entry.is_dir():
                entries.append({
                    'name': entry.name,
                    'type': 'directory',
                    'size': 0,
                    'lines': 0
                })
                
        # Sort entries: directories first, then files, both alphabetically
        entries.sort(key=lambda e: (e['type'] != 'directory', e['name'].lower()))
        
        return {
            "path": abs_path,
            "entries": entries
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }
