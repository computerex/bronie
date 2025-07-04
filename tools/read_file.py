import os

def read_file(filename, start_line=None, end_line=None):
    """
    Read the contents of a file with optional start and end line parameters.
    
    Args:
        filename (str): Path to the file to read
        start_line (int, optional): Line number to start reading from (1-indexed). Defaults to None.
        end_line (int, optional): Line number to end reading at (1-indexed). Defaults to None.
        
    Returns:
        str: Contents of the file or specified lines
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
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
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


def format_file_contents(file_data):
    """
    Format file contents as a rich Table for display
    
    Args:
        file_data (dict): Dictionary returned by read_file()
        
    Returns:
        rich.table.Table: Formatted table for display
    """
    from rich.table import Table
    
    table = Table(title=f"File: {file_data['filename']}")
    table.add_column("Line", justify="right", style="cyan")
    table.add_column("Content", style="white")
    
    for line in file_data['lines']:
        table.add_row(str(line['line_number']), line['text'].rstrip('\n'))
        
    return table
