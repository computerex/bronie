import os
from pathlib import Path

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
    List files in a directory with line counts.
    
    Args:
        directory_path (str, optional): Path to the directory. Defaults to current directory.
        
    Returns:
        str: Formatted list of files with line counts
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
        
        # Format the output
        result = [f"Contents of {abs_path}:"]
        result.append("\nName                           Type       Lines     Size")
        result.append("------------------------------------------------------------")
        
        for entry in entries:
            name = entry['name']
            entry_type = entry['type']
            lines = entry['lines'] if entry['type'] == 'file' else '-'
            size = f"{entry['size']:,} B" if entry['type'] == 'file' else '-'
            
            # Truncate long names
            if len(name) > 30:
                name = name[:27] + "..."
                
            result.append(f"{name:<30} {entry_type:<10} {lines:<9} {size}")
            
        return "\n".join(result)
        
    except Exception as e:
        return f"Error listing files: {e}"
