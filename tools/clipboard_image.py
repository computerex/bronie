import base64
import io
import os
import sys
import tempfile
import subprocess
from PIL import Image, ImageGrab

def get_clipboard_image():
    """
    Get an image from the clipboard and convert it to base64.
    
    Returns:
        tuple: (base64_string, mime_type) if successful, (None, None) if no image in clipboard
    """
    try:
        # For macOS (darwin)
        if sys.platform == 'darwin':
            # Create a temporary file
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            
            # Use osascript to save clipboard image to the temp file
            script = f'''
            set theFile to "{path}"
            try
                set theData to the clipboard as «class PNGf»
                set theFile to open for access theFile with write permission
                write theData to theFile
                close access theFile
                return true
            on error
                try
                    close access theFile
                end try
                return false
            end try
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            
            if result.stdout.strip() == 'true':
                with open(path, 'rb') as f:
                    image_data = f.read()
                os.unlink(path)  # Remove the temp file
                
                # Convert to base64
                base64_data = base64.b64encode(image_data).decode('utf-8')
                return base64_data, 'image/png'
            else:
                os.unlink(path)  # Remove the temp file
                return None, None
                
        # For Windows and Linux
        else:
            img = ImageGrab.grabclipboard()
            if img is not None:
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                base64_data = base64.b64encode(buffer.read()).decode('utf-8')
                return base64_data, 'image/png'
            return None, None
    except Exception as e:
        print(f"Error getting clipboard image: {e}", flush=True)
        return None, None

def is_image_in_clipboard():
    """
    Check if there is an image in the clipboard.
    
    Returns:
        bool: True if there is an image in the clipboard, False otherwise
    """
    try:
        base64_data, _ = get_clipboard_image()
        return base64_data is not None
    except:
        return False

if __name__ == "__main__":
    # Test the function
    base64_data, mime_type = get_clipboard_image()
    if base64_data:
        print(f"Image found in clipboard with mime type: {mime_type}")
        print(f"Base64 data (first 100 chars): {base64_data[:100]}...")
    else:
        print("No image found in clipboard") 