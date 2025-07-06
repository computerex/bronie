import json
import os

# Determine the absolute path to config.json within the package
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_DIR = os.path.dirname(_TOOL_DIR)
CONFIG_FILE = os.path.join(_PACKAGE_DIR, 'config.json')

# Default model configurations
DEFAULT_AGENT_MODEL = 'openai/gpt-4o'
DEFAULT_CODE_MODEL = 'anthropic/claude-3.5-sonnet'

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

def get_providers():
    config = _load_config()
    return config.get('providers', [])

def get_provider(provider_name):
    providers = get_providers()
    for p in providers:
        if p['name'] == provider_name:
            return p
    return None

# Default directories to ignore
DEFAULT_IGNORED_DIRS = {
    'env', 'venv', '.env', 'node_modules', 'vendor',
    '__pycache__', '.git', '.idea', '.vscode'
}

def get_ignored_dirs():
    config = _load_config()
    return set(config.get('ignored_dirs', DEFAULT_IGNORED_DIRS))

def set_ignored_dirs(dirs):
    config = _load_config()
    config['ignored_dirs'] = list(dirs)
    _save_config(config)

# Load ignored directories from config
IGNORED_DIRS = get_ignored_dirs()

# Convert IGNORED_DIRS to glob pattern for ripgrep
IGNORED_DIRS_GLOB = '!{' + ','.join(IGNORED_DIRS) + '}'
