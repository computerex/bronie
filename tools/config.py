import json
import os

# Default model configurations
DEFAULT_AGENT_MODEL = 'openai/gpt-4.1'
DEFAULT_CODE_MODEL = 'anthropic/claude-3.5-sonnet'
CONFIG_FILE = 'config.json'

# Common dependency and environment directories to ignore
IGNORED_DIRS = {
    'env', 'venv', '.env', 'node_modules', 'vendor',
    '__pycache__', '.git', '.idea', '.vscode'
}

# Convert IGNORED_DIRS to glob pattern for ripgrep
IGNORED_DIRS_GLOB = '!{' + ','.join(IGNORED_DIRS) + '}'

def _load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

def get_agent_model():
    config = _load_config()
    return config.get('agent_model', DEFAULT_AGENT_MODEL)

def set_agent_model(model):
    config = _load_config()
    config['agent_model'] = model
    _save_config(config)

def get_code_model():
    config = _load_config()
    return config.get('code_model', DEFAULT_CODE_MODEL)

def set_code_model(model):
    config = _load_config()
    config['code_model'] = model
    _save_config(config)
