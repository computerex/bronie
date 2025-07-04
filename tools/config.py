# Common configuration shared across tools

# Common dependency and environment directories to ignore
IGNORED_DIRS = {
    'env', 'venv', '.env', 'node_modules', 'vendor',
    '__pycache__', '.git', '.idea', '.vscode'
}

# Convert IGNORED_DIRS to glob pattern for ripgrep
IGNORED_DIRS_GLOB = '!{' + ','.join(IGNORED_DIRS) + '}' 