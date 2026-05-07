# chatcode

A Python terminal chat client for OpenAI-compatible LLMs. Interact with large language models directly from your command line with support for multiple providers, session management, and persistent chat history.

## Prerequisites

- **Python 3.11+** (3.12+ recommended)
- **opencode.json** configuration file containing provider and model definitions

## Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Commands

Start the chat client with the last used model (or interactive selection if none):

```bash
python -m chatcode
```

Start with a specific provider and model:

```bash
python -m chatcode --provider proxy-ollama --model qwen3.5:122b
```

Use a custom configuration file:

```bash
python -m chatcode --config ./opencode.json
```

Override the system prompt:

```bash
python -m chatcode --system "Du bist ein hilfreicher Assistent"
```

## In-Chat Commands

Once in the chat, use the following commands (prefixed with `:`):

| Command | Description |
|---------|-------------|
| `:help` | Display available commands |
| `:models` | List all providers and their models |
| `:use [provider model]` | Switch models (without args: interactive selection) |
| `:clear` | Clear chat history (system prompt remains) |
| `:system [text]` | Set or display the system prompt |
| `:info` | Show active provider, model, and base URL |
| `:save [filename]` | Save current session (optional filename, defaults to timestamp) |
| `:load <filename>` | Load a saved session from file |
| `:exit` | Exit the chat |

### Keyboard Shortcuts

- **Alt+Enter**: Insert a line break
- **Enter**: Send message
- **Ctrl+C**: Exit the chat

## Configuration: opencode.json

Create a configuration file at `~/.config/opencode/opencode.json` to define your providers and models.

### Structure

```json
{
  "provider": {
    "provider-id": {
      "options": {
        "baseURL": "https://api.example.com/v1",
        "apiKey": "your-api-key"
      },
      "models": {
        "model-id": {
          "displayName": "Model Display Name",
          "tools": false
        }
      }
    }
  }
}
```

### Example Configuration

```json
{
  "provider": {
    "openai": {
      "options": {
        "baseURL": "https://api.openai.com/v1",
        "apiKey": "sk-..."
      },
      "models": {
        "gpt-4": {
          "displayName": "GPT-4 Turbo",
          "tools": true
        },
        "gpt-3.5-turbo": {
          "displayName": "GPT-3.5 Turbo",
          "tools": false
        }
      }
    },
    "proxy-ollama": {
      "options": {
        "baseURL": "http://localhost:11434/v1",
        "apiKey": "dummy"
      },
      "models": {
        "qwen3.5:122b": {
          "displayName": "Qwen 3.5 122B",
          "tools": false
        },
        "llama2": {
          "displayName": "Llama 2",
          "tools": false
        }
      }
    },
    "anthropic": {
      "options": {
        "baseURL": "https://api.anthropic.com",
        "apiKey": "your-anthropic-key"
      },
      "models": {
        "claude-opus": {
          "displayName": "Claude Opus",
          "tools": true
        }
      }
    }
  }
}
```

### Configuration Notes

- **baseURL**: The API endpoint for your provider
- **apiKey**: Authentication key (use "dummy" for local services like Ollama)
- **displayName**: Human-readable name shown in the UI
- **tools**: Whether the model supports function calling (optional, defaults to `false`)

## Sessions

Sessions are automatically saved to `~/.config/chatcode/sessions/` and include:

- Chat message history
- Provider and model information
- System prompt
- Timestamps

Saved sessions can be in JSON or Markdown format (determined by file extension).

### Save Options

```bash
# Auto-generated filename with timestamp
:save

# Custom JSON filename
:save my-conversation

# Markdown export
:save my-conversation.md
```

## Architecture

The codebase is organized into modular components:

```
chatcode/
├── __main__.py        Entry point for python -m chatcode
├── cli.py             Command-line argument parsing and startup logic
├── config.py          Configuration file loading and parsing
├── models.py          Data models (ProviderConfig, ModelConfig, ChatMessage, Session)
├── client.py          LLM API client wrapper
├── picker.py          Interactive model selection UI
├── commands.py        Command dispatcher and handlers (:help, :use, :save, etc.)
├── chat.py            Main chat loop and session management
├── state.py           Last-used model persistence
└── session.py         Session serialization and file management
```

### Key Components

- **cli.py**: Handles command-line arguments and initializes the chat session
- **config.py**: Loads provider and model definitions from opencode.json with JSONC comment support
- **client.py**: Creates OpenAI-compatible API clients and streams chat responses
- **chat.py**: Runs the main chat loop with command dispatch and session management
- **commands.py**: Implements all in-chat commands (:help, :models, :use, etc.)
- **picker.py**: Interactive terminal UI for selecting providers and models
- **session.py**: Saves and loads chat sessions in JSON/Markdown format
- **state.py**: Persists the last-used provider/model selection
- **models.py**: Data classes for configuration and chat state

## Development

Run tests:

```bash
pytest
```

## License

See LICENSE file for details.
