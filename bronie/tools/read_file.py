import os

def read_file(filename, start_line=None, end_line=None):
    """
    Read the contents of a file with optional start and end line parameters.
    Supports reading entire files or specific line ranges.
    Handles encoding errors gracefully and provides detailed file information.
    
    Args:
        filename (str): Relative path to the file to read (from project directory)
        start_line (int, optional): Line number to start reading from (1-indexed). Defaults to None (start of file).
        end_line (int, optional): Line number to end reading at (1-indexed). Defaults to None (end of file).
        
    Returns:
        str or dict: 
            - If no line range specified: Returns file contents as string
            - If line range specified: Returns dict with:
                - filename: File path
                - total_lines: Total number of lines in file
                - start_line: First line read (1-indexed)
                - end_line: Last line read (1-indexed)
                - lines: List of dicts with line_number and text
            - Error string if file cannot be read
    """
    try:
        # Ensure the path is relative to the current working directory
        # which should be the project directory set in main.py
        filepath = os.path.join(os.getcwd(), filename)
        
        if not os.path.exists(filepath):
            return f"File not found: {filename}"
            
        if not os.path.isfile(filepath):
            return f"Not a file: {filename}"
            
        # Convert to integers if provided as strings
        if start_line is not None and isinstance(start_line, str):
            try:
                start_line = int(start_line)
            except ValueError:
                return f"Invalid start line: {start_line}. Must be an integer."
                
        if end_line is not None and isinstance(end_line, str):
            try:
                end_line = int(end_line)
            except ValueError:
                return f"Invalid end line: {end_line}. Must be an integer."
        
        # Read the entire file
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        
        # If no range specified, return the entire file
        if start_line is None and end_line is None:
            return ''.join(lines)
            
        # Adjust for 1-indexed input
        if start_line is not None:
            start_idx = max(0, start_line - 1)  # Convert to 0-indexed
        else:
            start_idx = 0
            
        if end_line is not None:
            end_idx = min(total_lines, end_line)  # Convert to 0-indexed + 1
        else:
            end_idx = total_lines
            
        # Validate range
        if start_idx >= total_lines:
            return f"Start line {start_line} is beyond the end of the file ({total_lines} lines)."
            
        if start_idx > end_idx:
            return f"Start line {start_line} is greater than end line {end_line}."
            
        # Extract the requested lines
        selected_lines = lines[start_idx:end_idx]
        
        # Prepare the output dictionary
        if start_line is None and end_line is None:
            return {
                'filename': filename,
                'total_lines': total_lines,
                'lines': [{'line_number': i+1, 'text': line} for i, line in enumerate(lines)]
            }
        else:
            return {
                'filename': filename,
                'total_lines': total_lines,
                'start_line': start_idx + 1,
                'end_line': end_idx,
                'lines': [{'line_number': i, 'text': line} 
                         for i, line in enumerate(selected_lines, start=start_idx + 1)]
            }
            
    except Exception as e:
        return f"Error reading file: {e}"
