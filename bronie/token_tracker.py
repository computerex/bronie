"""token_tracker.py – centralises token usage tracking to avoid circular imports."""

input_tokens = 0
output_tokens = 0

def track_tokens(arg1, arg2=None):
    """Increment token counters.

    Call patterns:
    1. track_tokens(prompt_tokens, completion_tokens)
    2. track_tokens(response_data_dict_with_usage)
    """
    global input_tokens, output_tokens
    if arg2 is None:
        response_data = arg1 if isinstance(arg1, dict) else {}
        usage = response_data.get("usage", {}) if response_data else {}
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
    else:
        prompt_tokens = int(arg1)
        completion_tokens = int(arg2)

    input_tokens += prompt_tokens
    output_tokens += completion_tokens

def get_totals():
    """Return (input_tokens, output_tokens)."""
    return input_tokens, output_tokens

def reset():
    """Reset token counters to zero."""
    global input_tokens, output_tokens
    input_tokens = 0
    output_tokens = 0 