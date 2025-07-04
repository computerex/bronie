import os
import time
from typing import Iterator
from openai import OpenAI


def complete_chat_stream(**kwargs) -> Iterator[str]:
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

    while tries < max_tries:
        response = None
        try:
            client = OpenAI(
                api_key=open_router_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            response = client.chat.completions.create(
                **kwargs
            )
            
            # Stream the chunks
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                
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

def complete_chat(**kwargs):
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
