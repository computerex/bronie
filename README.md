# Bronie - AI Agent Terminal

A cross-platform terminal UI for the Bronie AI agent system.

## Overview

Bronie is an AI agent system that executes file and system operations through controlled tool interfaces. The UI provides a modern, interactive terminal experience with features like:

- Rich terminal UI with panels and layouts
- Live updating conversation history
- File tree visualization
- Syntax highlighting for code and diffs
- Interactive animations for agent operations
- Project context display

## Features

### Terminal UI

The terminal UI is built using the Rich library, providing a modern and interactive experience:

- **Header**: Displays the application title
- **Main Area**: Split into two panels
  - **Output Panel**: Shows conversation history
  - **Sidebar**: Displays project context and file tree
- **Input Area**: For entering user messages

### Live Updates

The UI provides live updates during agent operations:

- Thinking animations when the agent is processing
- Spinner animations during tool execution
- Live file tree updates after file operations

### File Visualization

- File tree visualization with icons for different file types
- File size display
- Syntax highlighting for code files
- Diff visualization for file changes

### Agent Interaction

- **Available commands**: 
  - `:e <command>` - Execute shell command
  - `:m` - Toggle multiline mode
  - `:clear` - Reset message history
  - `:image` - Paste image from clipboard
  - `:drop` - Remove the last attached image
- Clear display of tool executions 
- Formatted display of tool results
- Error handling and display
- Direct shell command execution using `:e <command>` syntax
  - Execute single-line shell commands from input prompt
  - Immediate output display without LLM processing
  - Example: `:e ls -la` to list directory contents

### Image Support

- Paste images from clipboard with `:image` command
- Attach images to messages for visual context
- Images are automatically sent to the LLM when editing files
- Drop unwanted images with `:drop` command
- Visual indicator showing number of attached images

## Architecture

The UI is implemented as a separate module that integrates with the existing agent system:

- `ui.py`: Main UI class and rendering logic
- `file_tree.py`: File tree visualization utilities
- `main.py`: Updated to use the new UI

## Future Improvements

The UI framework is set up to support future improvements such as:

- Context-aware file tree highlighting
- Diff viewer for file changes
- Command history and autocomplete
- Drag and drop image support
- Multiple image attachment management

## Requirements

- Python 3.8+
- Rich library for terminal UI
- Pillow for image processing
- Other dependencies as listed in requirements.txt

## Usage

Run the main.py script to start the agent with the new UI:

```bash
python main.py [project_directory]
```

## License

[MIT License](LICENSE)

I have refactored the project as requested. It can now be installed using `pip install -e .` and launched with the `bronie` command. All functionality should remain unchanged. 
