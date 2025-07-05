import os
import re
from pathlib import Path
from .config import IGNORED_DIRS

def search_files(regex_pattern, directory='.'):
    """
    Search for files by regex patterns in their names and optionally their contents.
    Automatically ignores common dependency directories (node_modules, .git, etc.).
    Searches both filenames and file contents for matches.
    
    Args:
        regex_pattern (str): Regex pattern to match against file names and optionally file contents
        directory (str, optional): Directory to search in (relative to project directory). Defaults to current directory.
        
    Returns:
        dict: Search results containing:
            - status: 'success' or 'error'
            - message: Error message if status is 'error'
            - regex_pattern: Search pattern used
            - directory: Directory searched (absolute path)
            - matches: List of dicts containing:
                - filename: Relative file path (from search directory)
                - matched_lines: List of dicts with line_number and line_text (if content matches found)
            - message: Error message when status == 'error'
    """
    try:
        # Compile the regex pattern
        try:
            regex = re.compile(regex_pattern)
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
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in IGNORED_DIRS]
            
            for file in files:
                if regex.search(file):
                    rel_path = os.path.relpath(os.path.join(root, file), abs_path)
                    
                    # Skip files in ignored directories
                    if any(ignored in rel_path.split(os.sep) for ignored in IGNORED_DIRS):
                        continue
                        
                    full_path = os.path.join(root, file)
                    
                    match_result = {
                        'filename': rel_path,
                        'matched_lines': []
                    }
                    
                    # Search file contents if it's a text file
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                if regex.search(line):
                                    match_result['matched_lines'].append({
                                        'line_number': line_num,
                                        'line_text': line.rstrip()
                                    })
                    except (UnicodeDecodeError, IOError):
                        # Skip binary files or files we can't read
                        pass
                        
                    matches.append(match_result)
                    
        # Sort matches by filename
        matches.sort(key=lambda x: x['filename'])
        
        return {
            'status': 'success',
            'regex_pattern': regex_pattern,
            'directory': abs_path,
            'matches': matches
        }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'regex_pattern': regex_pattern,
            'directory': directory,
            'matches': []
        }
