input_tokens = 0
output_tokens = 0

def reset_token_counts():
    """Reset global token counters to zero."""
    global input_tokens, output_tokens
    input_tokens = 0
    output_tokens = 0

# Debug message when module loads
print(f"DEBUG: token_state.py loaded - input_tokens={input_tokens}, output_tokens={output_tokens}") 