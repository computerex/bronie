import base64
import os
from difflib import unified_diff
from llm import complete_chat, complete_chat_stream
from coders.editblock_coder import get_edits, apply_edits
from rich.console import Console
from tools.config import get_code_model


EDIT_PROMPT = """Act as an expert software developer.
Always use best practices when coding.
Respect and use existing conventions, libraries, etc that are already present in the code base.
Take requests for changes to the supplied code.

Once you understand the request you MUST:

1. Think step-by-step and explain the needed changes in a few short sentences.

2. Extract and return ONLY the *SEARCH/REPLACE blocks* from the input, maintaining their exact format:
   ```
   <<<<<<< SEARCH
   [exact lines to find in current code]
   =======
   [new code to replace those lines]
   >>>>>>> REPLACE
   ```

3. If the input already contains properly formatted *SEARCH/REPLACE blocks*, simply return them as-is.
4. If the input contains a plan or explanation, extract only the *SEARCH/REPLACE blocks* from it.
5. If no blocks are found, create appropriate blocks based on the instructions.

Important:
- Only return the *SEARCH/REPLACE blocks*, nothing else
- Keep each block focused and minimal
- Make sure SEARCH sections EXACTLY match existing code - this means:
  * Every space, tab, and newline must match exactly
  * Indentation must be preserved exactly as it appears in the original code
  * Line endings must match exactly
  * No extra or missing whitespace is allowed
- For moving code, use two blocks: one to remove from old location, one to insert in new location
- Each block should be self-contained and not depend on other blocks
- If a block depends on another block, combine them into a single block
- When copying code into SEARCH sections, copy it exactly as it appears - do not try to clean up or reformat the whitespace"""

def get_image_mime_type(base64_data):
    """Detects the MIME type of an image from its base64 encoded data."""
    try:
        # Decode the base64 string, handling potential padding errors
        # Ensure the padding is correct before decoding
        missing_padding = len(base64_data) % 4
        if missing_padding:
            base64_data += '=' * (4 - missing_padding)
        image_data = base64.b64decode(base64_data, validate=True)

        # Check magic numbers
        if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        elif image_data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            return 'image/gif'
        elif image_data.startswith(b'RIFF') and image_data[8:12] == b'WEBP':
             return 'image/webp'
        # Add checks for other formats like BMP, TIFF if needed
        else:
            # Default if format is unknown or add more specific error handling
            print("Warning: Could not detect image format from base64 data. Defaulting to png.", flush=True)
            return 'image/png'
    except Exception as e:
        # Handle potential base64 decoding errors
        print(f"Error decoding base64 or invalid image data: {e}", flush=True)
        # Return a default or raise a more specific error
        return 'image/png' # Defaulting to png on error
    
def get_thinking(instruction, code, images=None, model=None, **kwargs):        
    messages = [
        {"role": "user", "content": [{"type": "text", "text": EDIT_PROMPT}]},
        {"role": "user", "content": [{"type": "text", "text": f"""Code:\n{code}\n\n{instruction}"""}]}
    ]
    
    if images:
        for img_base64 in images:
            # Detect the MIME type of the image
            mime_type = get_image_mime_type(img_base64)
            messages[-1]['content'].append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{img_base64}"}
            })

    return complete_chat(messages=messages, model=model, **kwargs)

def diff(a: str, b: str) -> str:
    """
    Generate a git-style diff between two strings a and b.
    
    :param a: Original string
    :param b: Modified string
    :return: A git-style diff as a string
    """
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    
    # Use difflib to compute the differences
    diff_lines = unified_diff(
        a_lines, 
        b_lines, 
        lineterm='',  # Avoid adding extra newlines
        fromfile='a',
        tofile='b'
    )
    
    # Join the result to form a single string
    return '\n'.join(diff_lines)

def edit_file(filename, instruction, images=None):
    """
    Edit a file by applying changes based on natural language instructions.
    Supports both text-based editing and visual editing with attached images.
    Creates directories if they don't exist and creates new files if they don't exist.
    
    Args:
        filename (str): Relative path to the file to edit (from project directory)
        instruction (str): Natural language description of what changes to make
        images (list, optional): List of base64-encoded images for visual context. Defaults to None.
        
    Returns:
        tuple: (stdout, stderr) - Empty strings on success, error messages on failure
    """
    try:
        # Ensure the path is relative to the current working directory
        # which should be the project directory set in main.py
        filepath = os.path.join(os.getcwd(), filename)
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'r') as f:
                code = f.read()
        except FileNotFoundError:
            code = ""

        print(f"Instruction: {instruction}", flush=True)
        
        # Construct messages for the chat
        messages = [
            {"role": "user", "content": [{"type": "text", "text": EDIT_PROMPT}]},
            {"role": "user", "content": [{"type": "text", "text": f"""Code:\n{code}\n\n{instruction}"""}]}
        ]

        if images:
            for img_base64 in images:
                # Detect the MIME type of the image
                mime_type = get_image_mime_type(img_base64)
                messages[-1]['content'].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{img_base64}"}
                })
        
                # Get the user-selected code model
        code_model = get_code_model()
        
        # Stream the response in real-time
        for chunk in complete_chat_stream(messages=messages, model=code_model):
            print(chunk, end="", flush=True)
        
        # Get final complete response for processing
        response = get_thinking(instruction, code, images, model=code_model)
        edits = get_edits(response)
        new_code = apply_edits(code, edits)

        if new_code != code:
            diff_output = diff(code, new_code)
            console = Console()
            if diff_output:
                console.print("\n[bold green]Changes:[/bold green]")
                for line in diff_output.splitlines():
                    if line.startswith('+'):
                        console.print(line, style="green")
                    elif line.startswith('-'):
                        console.print(line, style="red")
                    elif line.startswith('@'):
                        console.print(line, style="yellow")
                    else:
                        console.print(line)

            print(f"\nWriting to {filepath}", flush=True)
            with open(filepath, 'w+') as f:
                f.write(new_code)
            return "", ""
        else:
            return "", ""
    except Exception as e:
        return f"Error editing file: {e}", ""
