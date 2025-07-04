import os
import re
import subprocess
from pathlib import Path
from .config import IGNORED_DIRS_GLOB

from rich.table import Table

def grep_search(pattern, file_pattern="*"):
    """
    Search for patterns in files using ripgrep or a Python-based alternative.
    Automatically ignores common dependency directories.
    
    Args:
        pattern (str): The pattern to search for
        file_pattern (str, optional): File pattern to search in. Defaults to "*".
        
    Returns:
        list: List of dictionaries containing matches with keys:
              - filename: relative path to the file
              - line_number: line number of the match
              - line_text: the matched line content
    """
    try:
        # Get current working directory (project directory)
        project_dir = os.getcwd()
        
        # Try to use ripgrep if available
        try:
            # Build ripgrep command with ignore patterns
            cmd = [
                "rg",
                "--glob", file_pattern,  # File pattern
                "--glob", IGNORED_DIRS_GLOB,  # Ignore patterns
                "--no-heading",  # Don't group matches by file
                "--line-number",  # Show line numbers
                "--color", "never",  # No color codes in output
                pattern,  # Search pattern
                "."  # Search in current directory
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode in [0, 1]:  # rg returns 1 if no matches found
                if not result.stdout:
                    return []
                matches = []
                for line in result.stdout.splitlines():
                    if ':' in line:
                        filename, rest = line.split(':', 1)
                        if ':' in rest:
                            line_number, line_text = rest.split(':', 1)
                            matches.append({
                                'filename': filename.lstrip('./'),
                                'line_number': int(line_number),
                                'line_text': line_text.strip()
                            })
                return matches
            else:
                # Fall back to Python implementation if ripgrep fails
                raise subprocess.SubprocessError("ripgrep command failed")
        except (subprocess.SubprocessError, FileNotFoundError):
            # Fall back to Python implementation
            pass
                
        # Python-based implementation (fallback)
        matches = []
        cwd = Path(project_dir)
        
        for path in cwd.rglob(file_pattern):
            # Skip ignored directories
            if any(ignored in str(path.parent).split(os.sep) for ignored in IGNORED_DIRS):
                continue
                
            if path.is_file():
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                # Convert path to be relative to project directory
                                rel_path = str(path.relative_to(cwd))
                                matches.append({
                                    'filename': rel_path,
                                    'line_number': i,
                                    'line_text': line.rstrip()
                                })
                except Exception as e:
                    # Convert path to be relative to project directory
                    rel_path = str(path.relative_to(cwd))
                    matches.append({
                        'filename': rel_path,
                        'line_number': 0,
                        'line_text': f"Error reading file: {e}"
                    })
        
        return matches
            
    except Exception as e:
        return [{
            'filename': 'error',
            'line_number': 0,
            'line_text': f"Error during search: {e}"
        }]

def create_search_results_table(results):
    """
    Create a rich Table from grep search results.
    
    Args:
        results (list): List of dictionaries with search results
        
    Returns:
        Table: Rich Table object for display
    """
    table = Table(show_header=True, header_style="bold")
    table.add_column("File")
    table.add_column("Line", justify="right")
    table.add_column("Content")
    
    for result in results:
        table.add_row(
            result['filename'],
            str(result['line_number']),
            result['line_text']
        )
    
    return table
