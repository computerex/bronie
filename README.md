# Bronie: The AI Software Engineering Assistant for Your Terminal

Bronie is an AI-powered assistant that seamlessly integrates with your development environment. By using Large Language Models (LLMs) and a suite of specialized tools, Bronie helps you understand, navigate, and modify code directly from your terminal.

![Bronie in action]([[https://i.postimg.cc/SsKLDc7B/image.png](https://i.ibb.co/jvrCdqc3/image.png)](https://i.ibb.co/jvrCdqc3/image.png))

## Overview

Bronie works by connecting an AI model with your local project directory, allowing it to perform coding tasks through natural language commands. It has deep contextual understanding of your codebase and can execute precise modifications without leaving your terminal.

## Core Concepts

- **Agent-Tool Architecture**: The core `Agent` orchestrates tasks by intelligently selecting and using various `Tools` (like `edit_file`, `list_files`) based on your requests.
- **Dynamic Tool Discovery**: The system automatically discovers tools from the `bronie/tools` directory, making it easily extensible with new capabilities.
- **Precise File Editing**: The `edit_file` tool uses a `SEARCH/REPLACE` block mechanism for reliable, targeted code modifications without affecting surrounding code.

## Features

- 💬 **Conversational Coding**: Interact with your codebase using natural language
- 📁 **File System Integration**: Browse, search, and modify files within your project context
- 🔧 **Shell Command Execution**: Run commands and integrate their output into the conversation
- 👀 **Visual Context**: Get descriptions and details about files and project structure
- 🧩 **Automatic Tool Registration**: Easily extend with new tools that are automatically discovered
- 🔄 **Reliable Code Editing**: Make precise changes with the `SEARCH/REPLACE` block mechanism

## Getting Started

### Prerequisites

- Python 3.8 or higher
- API key(s) for your chosen LLM provider (OpenAI, Anthropic, OpenRouter, etc.)

### Installation

```bash
pip install -e .
```

### Configuration

Create a `.env` file in your home directory with your API credentials:

```
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-...
# OR
OPEN_ROUTER_API_KEY=sk-...
```

### Usage

Start the assistant with your project directory:

```bash
bronie /path/to/your/project
```

### Advanced Configuration

You can configure models and providers in `bronie/config.json`:

- `agent_model`: The primary model that runs the main assistant
- `code_model`: Model specifically optimized for code-heavy tasks
- `light_model`: Lighter model used for simple operations

Define API providers in the `providers` array:

```json
{
  "providers": [
    {
      "name": "openai",
      "api_key_env": "OPENAI_API_KEY",
      "base_url": "https://api.openai.com/v1"
    },
    {
      "name": "anthropic",
      "api_key_env": "ANTHROPIC_API_KEY"
    }
  ]
}
```

**OpenRouter Support**: Use any model with the `openrouter/` prefix (e.g., `openrouter/google/gemini-pro`)

## Available Tools

Bronie comes with several built-in tools:

- **list_files**: Display the structure of project directories and files
- **read_file**: View the contents of a specific file
- **edit_file**: Make changes to files using precise SEARCH/REPLACE patterns
- **exec_shell**: Execute shell commands and see their output
- **grep_search**: Search across files for specific patterns or text
- **search_files**: Find files by name patterns or content matching
- **talk_to_user**: Request additional information from you when needed

## How to Contribute

You can easily extend Bronie by adding new tools:

1. Create a new Python file in `bronie/tools/`
2. Define a function with the same name as the file
3. Include a docstring that describes what the tool does
4. Your tool will be automatically discovered and available to use

Example of a simple tool (`bronie/tools/my_new_tool.py`):

```python
def my_new_tool(message: str):
    """
    This is an example tool that prints a message.

    Args:
        message (str): The message to print.
    """
    # Tool implementation
    return f"The message was: {message}"
```

## License

MIT Licensed
