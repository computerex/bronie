import os
import time
import requests
from typing import Iterator, List, Optional, Dict, Tuple
from openai import OpenAI
import tiktoken

from .tools.config import (
    get_agent_model as config_get_agent_model, 
    get_code_model as config_get_code_model, 
    get_light_model as config_get_light_model,
    get_providers
)

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

class LLMManager:
    def __init__(self):
        self.providers = get_providers()
        self._openrouter_models_cache = None

    def _fetch_openrouter_models(self) -> List[Dict]:
        """Fetch the list of models from OpenRouter."""
        if self._openrouter_models_cache:
            return self._openrouter_models_cache

        api_key = os.getenv("OPEN_ROUTER_API_KEY")
        if not api_key:
            # Silently fail if key is not present, as it's not required for other providers
            return []
        
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            self._openrouter_models_cache = response.json().get('data', [])
            return self._openrouter_models_cache
        except requests.RequestException as e:
            print(f"Could not fetch OpenRouter models: {e}")
            return []

    def list_models(self) -> List[Dict]:
        """Get a list of all available models from all providers."""
        models = []
        for provider in self.providers:
            provider_name = provider['name']
            if provider_name == 'openrouter':
                or_models = self._fetch_openrouter_models()
                for model_info in or_models:
                    model_info['id'] = f"openrouter/{model_info['id']}"
                models.extend(or_models)
            else:
                for model_name in provider.get("models", []):
                    models.append({
                        "id": f"{provider_name}/{model_name}",
                        "name": model_name,
                        "provider": {"name": provider_name},
                        "context_length": "N/A"
                    })
        return models

    def _get_provider_for_model(self, model_id: str) -> Optional[Dict]:
        """Get the provider for a given model ID."""
        if "/" not in model_id:
            return None
        provider_name, _ = model_id.split('/', 1)
        for provider in self.providers:
            if provider['name'] == provider_name:
                return provider
        return None

    def get_client_for_model(self, model_id: str) -> Tuple[OpenAI, str]:
        """Get an OpenAI client and the model name for a given model ID."""
        provider = self._get_provider_for_model(model_id)
        if not provider:
            raise ValueError(f"No provider found for model {model_id}")

        api_key = provider.get("api_key")
        if not api_key:
            api_key_env_var = provider.get("api_key_env_var")
            if not api_key_env_var:
                raise ValueError(f"Neither 'api_key' nor 'api_key_env_var' are configured for provider {provider['name']}")

            api_key = os.getenv(api_key_env_var)
            if not api_key:
                raise ValueError(f"API key environment variable '{api_key_env_var}' not set and no 'api_key' provided for provider {provider['name']}")

        client = OpenAI(
            api_key=api_key,
            base_url=provider.get("api_base"),
        )
        _, model_name = model_id.split('/', 1)
        return client, model_name

llm_manager = LLMManager()

def list_models() -> List[Dict]:
    """Get list of available models."""
    return llm_manager.list_models()

def set_agent_model(model_id: str) -> None:
    """Set the default model for agent/chat interactions."""
    from .tools.config import set_agent_model as config_set_agent_model
    config_set_agent_model(model_id)
    
def set_code_model(model_id: str) -> None:
    """Set the default model for code editing."""
    from .tools.config import set_code_model as config_set_code_model
    config_set_code_model(model_id)

def get_agent_model() -> str:
    """Get the configured agent model"""
    return config_get_agent_model()

def get_code_model() -> str:
    """Get the configured code model"""
    return config_get_code_model()

def get_light_model() -> str:
    """Get the configured light model"""
    return config_get_light_model()

def complete_chat_stream(model: Optional[str] = None, **kwargs) -> Iterator[str]:
    """
    Stream chat completions from a configured provider, yielding text chunks as they arrive.
    """
    model_id = model or get_agent_model()
    client, model_name = llm_manager.get_client_for_model(model_id)
    
    kwargs['model'] = model_name

    tries = 0
    max_tries = 3
    backoff_time = 2

    if 'timeout' not in kwargs:
        kwargs['timeout'] = 60*10
    
    kwargs['stream'] = True

    input_tokens_msg = _count_tokens_messages(kwargs.get("messages", []))

    while tries < max_tries:
        response = None
        try:
            response = client.chat.completions.create(**kwargs)
            
            response_text = ""
            try:
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        part = chunk.choices[0].delta.content
                        yield part
                        response_text += part
            except KeyboardInterrupt:
                return

            output_tokens_calc = _count_tokens_text(response_text)
            from .token_tracker import track_tokens
            track_tokens(input_tokens_msg, output_tokens_calc)
            
            return
            
        except Exception as e:
            print('EXCEPTION: ', flush=True)
            print(e, flush=True)
            if response:
                print(response, flush=True)
            
            if "401" in str(e):
                raise ValueError(f"Invalid or missing API key for model {model_id}") from e
            
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
    """
    Get a chat completion from a configured provider.
    """
    model_id = model or get_agent_model()
    client, model_name = llm_manager.get_client_for_model(model_id)

    kwargs['model'] = model_name

    tries = 0
    max_tries = 3
    backoff_time = 2

    if 'timeout' not in kwargs:
        kwargs['timeout'] = 60*10

    while tries < max_tries:
        response = None
        try:
            response = client.chat.completions.create(**kwargs)
            
            if hasattr(response, 'error') and isinstance(response.error, dict) and response.error.get('code') == 429:
                print(f"Rate limit exceeded in response. Retrying in {backoff_time} seconds...", flush=True)
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            
            text_response = response.choices[0].message.content
            
            input_tokens_msg = _count_tokens_messages(kwargs.get("messages", []))
            output_tokens_calc = _count_tokens_text(text_response)
            from .token_tracker import track_tokens
            track_tokens(input_tokens_msg, output_tokens_calc)
            
            return text_response
        except Exception as e:
            print('EXCEPTION: ', flush=True)
            print(e, flush=True)
            if response:
                print(response, flush=True)
            
            error_message = str(e)
            if "401" in error_message:
                raise ValueError(f"Invalid or missing API key for model {model_id}") from e
            
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
    return ""
