import os
import time
import requests
from typing import Iterator, List, Optional, Dict
from openai import OpenAI
import tiktoken

from tools.config import get_agent_model as config_get_agent_model, get_code_model as config_get_code_model

DEFAULT_AGENT_MODEL = "openai/gpt-4.1"
DEFAULT_CODE_MODEL = "anthropic/claude-3.5-sonnet"

# Add helper function to count tokens
ENCODER = tiktoken.encoding_for_model("gpt-4")

def _count_tokens_text(text: str) -> int:
    return len(ENCODER.encode(text))

def _count_tokens_messages(messages) -> int:
    total = 0
    for m in messages:
        if isinstance(m.get("content"), str):
            total += _count_tokens_text(m["content"])
        elif isinstance(m.get("content"), list):
            for c in m["content"]:
                if isinstance(c, dict) and "text" in c:
                    total += _count_tokens_text(c["text"])
    return total

def list_openrouter_models() -> List[Dict]:
    """Get list of available models from OpenRouter API.
    
    Returns:
        List[Dict]: List of model info dictionaries
        
    Raises:
        ValueError: If no API key is configured
    """
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("No OpenRouter API key provided")
        
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    response.raise_for_status()
    return response.json()['data']


def set_agent_model(model_id: str) -> None:
    """Set the default model for agent/chat interactions.
    
    Args:
        model_id: OpenRouter model identifier
    """
    from tools.config import set_agent_model as config_set_agent_model
    config_set_agent_model(model_id)
    
def set_code_model(model_id: str) -> None:
    """Set the default model for code editing.
    
    Args:
        model_id: OpenRouter model identifier  
    """
    from tools.config import set_code_model as config_set_code_model
    config_set_code_model(model_id)

def get_agent_model() -> str:
    """Get the configured agent model, falling back to default"""
    return config_get_agent_model()

def get_code_model() -> str:
    """Get the configured code model, falling back to default"""
    return config_get_code_model()


def complete_chat_stream(model: Optional[str] = None, **kwargs) -> Iterator[str]:
    """
    Stream chat completions from OpenRouter/OpenAI, yielding text chunks as they arrive.
    Similar to complete_chat() but streams the response instead of waiting for completion.
    
    Args:
        **kwargs: Same arguments as complete_chat(), but stream=True is forced
        
    Yields:
        str: Text chunks as they arrive from the API
        
    Raises:
        ValueError: If no API key is provided
        Exception: On API errors after retries are exhausted
    """
    DEFAULT_OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
    open_router_api_key = DEFAULT_OPEN_ROUTER_API_KEY

    if not open_router_api_key:
        raise ValueError("No OpenRouter API key provided")

    tries = 0
    max_tries = 3
    backoff_time = 2

    if 'timeout' not in kwargs:
        kwargs['timeout'] = 60*10
    
    # Force streaming mode
    kwargs['stream'] = True

    # Right before while tries < max_tries loop we compute input_tokens_msg
    input_tokens_msg = _count_tokens_messages(kwargs.get("messages", []))

    while tries < max_tries:
        response = None
        try:
            client = OpenAI(
                api_key=open_router_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            
            # Use provided model or get default
            if 'model' not in kwargs:
                kwargs['model'] = model or get_agent_model()
                
            response = client.chat.completions.create(
                **kwargs
            )
            
            # start of streaming: set response_text
            response_text = ""  # move near top of try before for chunk loop
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    part = chunk.choices[0].delta.content
                    yield part
                    response_text += part
            # after streaming loop
            output_tokens_calc = _count_tokens_text(response_text)
            from main import track_tokens
            track_tokens(input_tokens_msg, output_tokens_calc)
            
            return  # Success - exit the retry loop
            
        except Exception as e:
            print('EXCEPTION: ', flush=True)
            print(e, flush=True)
            if response:
                print(response, flush=True)
            
            if "401" in str(e) or "No auth credentials found" in str(e):
                raise ValueError("Invalid or missing OpenRouter API key") from e
            
            error_code = None
            if hasattr(e, 'error') and isinstance(e.error, dict) and 'code' in e.error:
                error_code = e.error['code']
            
            if error_code == 429:
                print(f"Rate limit exceeded. Retrying in {backoff_time} seconds...", flush=True)
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            
            tries += 1
            if tries >= max_tries:
                raise
            continue
    return

def complete_chat(model: Optional[str] = None, **kwargs) -> str:
    DEFAULT_OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
    # Use provided API key if available in kwargs, otherwise fallback to environment
    open_router_api_key = DEFAULT_OPEN_ROUTER_API_KEY

    if not open_router_api_key:
        raise ValueError("No OpenRouter API key provided")

    tries = 0
    max_tries = 3
    backoff_time = 2  # Initial backoff time in seconds

    # check if timeout is set
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 60*10

    while tries < max_tries:
        response = None
        try:
            client = OpenAI(
                api_key=open_router_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            
            # Use provided model or get default
            if 'model' not in kwargs:
                kwargs['model'] = model or get_agent_model()
                
            response = client.chat.completions.create(
                **kwargs
            )
            
            # Check if response has an error attribute indicating rate limiting
            if hasattr(response, 'error') and isinstance(response.error, dict) and response.error.get('code') == 429:
                print(f"Rate limit exceeded in response. Retrying in {backoff_time} seconds...", flush=True)
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
                continue  # Skip to next iteration without incrementing tries
            
            text_response = response.choices[0].message.content
            reasoning = response.choices[0].message.reasoning if hasattr(response.choices[0].message, 'reasoning') else ""
            if reasoning and len(reasoning) > 0:
                text_response = f"{reasoning}\n{text_response}"

            # Same for complete_chat non-streaming: after we get text_response
            input_tokens_msg = _count_tokens_messages(kwargs.get("messages", []))
            output_tokens_calc = _count_tokens_text(text_response)
            from main import track_tokens
            track_tokens(input_tokens_msg, output_tokens_calc)
            
            return text_response
        except Exception as e:
            print('EXCEPTION: ', flush=True)
            print(e, flush=True)
            if response:
                print(response, flush=True)
            
            # Check specifically for authentication errors
            error_message = str(e)
            if "401" in error_message or "No auth credentials found" in error_message:
                raise ValueError("Invalid or missing OpenRouter API key") from e
            
            # Handle rate limit errors (429)
            # Check if error has a code attribute that equals 429
            error_code = None
            if hasattr(e, 'error') and isinstance(e.error, dict) and 'code' in e.error:
                error_code = e.error['code']
            
            if error_code == 429:
                print(f"Rate limit exceeded. Retrying in {backoff_time} seconds...", flush=True)
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
                continue  # Skip the tries increment to not count rate limits against max_tries
            
            tries += 1
            if tries >= max_tries:
                raise  # Re-raise the last exception if we've exhausted our tries
            continue
    return ""
