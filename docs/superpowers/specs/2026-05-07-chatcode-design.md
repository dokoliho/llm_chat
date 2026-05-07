# chatcode — Design Spec

**Date:** 2026-05-07  
**Status:** Approved  

---

## Overview

`chatcode` is a Python terminal chat client for OpenAI-compatible LLM endpoints. It reads provider and model configuration directly from an existing `opencode.json` file. It is a pure CLI/TUI tool — no web interface, no agent framework, no tool-calling. Focus: robust local use, clean code, simple maintainability.

---

## Project Location

Files live directly in `/Users/oliver/Development/Technologien/llm_chat/` alongside the existing Node.js files.

---

## Startup & Invocation

```
python -m chatcode                                  # interactive model selection or last-used
python -m chatcode --provider proxy-ollama --model qwen3.5:122b
python -m chatcode --config ./opencode.json
python -m chatcode --system "Du bist ein hilfreicher Assistent"
```

**Startup logic:**
1. Load `~/.config/opencode/opencode.json` (or `--config` override)
2. Read `~/.config/chatcode/state.json` for last-used provider+model
3. If last-used exists in current config → use it directly, print confirmation
4. Otherwise (first start or model no longer in config) → interactive arrow-key selection
5. `--provider` / `--model` flags bypass all of the above

---

## File Structure

```
llm_chat/
├── chatcode/
│   ├── __init__.py
│   ├── __main__.py       # entry: python -m chatcode → cli.main()
│   ├── config.py         # JSONC-tolerant parser + opencode.json loader
│   ├── models.py         # dataclasses: ProviderConfig, ModelConfig, ChatMessage, Session
│   ├── client.py         # OpenAI SDK wrapper, streaming, error handling
│   ├── chat.py           # main loop: PromptSession, input → response
│   ├── commands.py       # command registry & handlers
│   ├── state.py          # last-used model persistence
│   └── session.py        # save/load sessions as JSON or Markdown
├── tests/
│   ├── test_config.py
│   ├── test_models.py
│   └── test_commands.py
├── .idea/
│   └── runConfigurations/
│       └── chatcode.xml  # PyCharm run configuration
├── requirements.txt
└── README.md
```

---

## Data Models (`models.py`)

```python
@dataclass
class ModelConfig:
    id: str                     # real model ID, e.g. "gemma4-ctx32k"
    display_name: str           # displayName or fallback to id
    tools: bool = False

@dataclass
class ProviderConfig:
    id: str                     # e.g. "lokales-ollama"
    base_url: str
    api_key: str = "dummy"      # fallback if not in config
    models: dict[str, ModelConfig] = field(default_factory=dict)

@dataclass
class ChatMessage:
    role: str                   # "user" | "assistant" | "system"
    content: str
    timestamp: datetime

@dataclass
class Session:
    id: str                     # timestamp-based: "2026-05-07T14-23"
    provider_id: str
    model_id: str
    system_prompt: str | None
    messages: list[ChatMessage]
```

---

## Config Parsing (`config.py`)

- Default path: `~/.config/opencode/opencode.json`
- Override via `--config <path>`
- JSONC support: strip `// line comments` and `/* block comments */` with regex before `json.loads()`
- No external JSONC library needed
- Graceful degradation:
  - Missing `apiKey` → use `"dummy"`
  - Missing `displayName` → use model ID
  - Missing or empty `models` → provider still loads, just has no models
  - Invalid JSON after comment stripping → clear error message, no traceback spam

---

## State Persistence (`state.py`)

- File: `~/.config/chatcode/state.json`
- Contents: `{"last_provider": "proxy-ollama", "last_model": "qwen3.5:122b"}`
- Written immediately on every model switch (`:use`, startup selection, CLI flags)
- If file missing or corrupt: silently fall back to interactive selection

---

## API Client (`client.py`)

```python
def make_client(provider: ProviderConfig) -> openai.OpenAI
def stream_chat(
    client: openai.OpenAI,
    model_id: str,
    messages: list[ChatMessage],
    on_token: Callable[[str], None],
) -> str  # returns full response text for history
```

**Streaming:** `client.chat.completions.create(stream=True)` → iterate chunks → call `on_token` per token → `rich.print` to stdout.

**Error handling:**
- `APIConnectionError` → "Verbindung zu \<baseURL\> fehlgeschlagen. Läuft der Server?"
- `APIStatusError` → HTTP status + response message
- `APITimeoutError` → "Timeout — Server antwortet nicht"
- All errors: user-friendly message via `rich`, session stays alive, no crash

---

## Chat Loop (`chat.py`)

Uses `prompt_toolkit.PromptSession` with:
- History file: `~/.config/chatcode/history`
- Multiline input: `Meta+Enter` to submit, or auto-detect via trailing backslash
- Auto-completion for `:` commands

**Loop:**
```
read input
  ├─ starts with ":"  →  commands.dispatch(text, context)
  ├─ empty            →  skip
  └─ else             →  add to messages, stream_chat, append response to history
```

**Output with `rich`:**
- User prompt line: subtle color prefix (`You:`)
- Streamed assistant tokens: printed directly as they arrive
- After stream ends: no re-render (avoid flicker)
- Errors: `rich.Panel` in red
- `:models`, `:info`, `:help`: formatted tables/panels

---

## Commands (`commands.py`)

Registry: `dict[str, CommandHandler]` where `CommandHandler = Callable[[args, context], None]`

| Command | Args | Effect |
|---|---|---|
| `:help` | — | Print all commands with descriptions |
| `:models` | — | List all providers + models from loaded config |
| `:use` | `[provider model]` | Switch model; no args → interactive arrow-key selection |
| `:clear` | — | Clear message history; keep system prompt |
| `:system` | `[text]` | Set/show system prompt |
| `:info` | — | Show active provider, model ID, display name, baseURL |
| `:save` | `[filename]` | Save session; default filename = timestamp |
| `:load` | `<filename>` | Load session from file |
| `:exit` | — | Exit cleanly |

`:use` without args opens the same interactive arrow-key picker used at startup.

---

## Session Management (`session.py`)

- Save location: `~/.config/chatcode/sessions/`
- Default filename: `2026-05-07T14-23-45.json`
- JSON format:
  ```json
  {
    "id": "2026-05-07T14-23-45",
    "provider": "proxy-ollama",
    "model": "qwen3.5:122b",
    "system_prompt": null,
    "messages": [
      {"role": "user", "content": "...", "timestamp": "..."},
      {"role": "assistant", "content": "...", "timestamp": "..."}
    ]
  }
  ```
- Markdown export (`.md` extension): human-readable with `## User` / `## Assistant` headings
- `:load` restores provider+model+system_prompt+messages, updates state

---

## PyCharm Run Configuration (`.idea/runConfigurations/chatcode.xml`)

- Script: module mode (`python -m chatcode`)
- Working directory: project root
- Interpreter: project Python
- Optional parameters field pre-filled for easy override

---

## Dependencies (`requirements.txt`)

```
openai>=1.0
prompt_toolkit>=3.0
rich>=13.0
```

Python 3.12 (available on this machine). No uv required — plain `pip install -r requirements.txt`.

---

## Tests

No real HTTP calls. All API interactions mocked with `unittest.mock.patch`.

**`test_config.py`:**
- Parse JSONC with `//` and `/* */` comments
- Missing `apiKey` → `"dummy"` fallback
- Missing `displayName` → model ID fallback
- Invalid JSON → clean error (no traceback)

**`test_models.py`:**
- Provider lookup by ID
- Model lookup by ID (display name fallback)
- Unknown provider/model raises descriptive exception

**`test_commands.py`:**
- `:use proxy-ollama qwen3.5:122b` parses correctly
- `:use` without args calls interactive picker (mocked)
- Unknown command returns help hint
- `:clear` removes messages, preserves system prompt

---

## Assumptions

1. `opencode.json` follows the structure shown — `provider.<id>.options.{baseURL,apiKey}` and `provider.<id>.models.<id>.{displayName,tools}`.
2. All providers are OpenAI-compatible (the `npm: @ai-sdk/openai-compatible` field is ignored by chatcode).
3. `tools: true` in model config is stored but not acted upon — chatcode is a chat client only.
4. No authentication beyond `apiKey` header is needed.
5. Sessions directory and state file are created on first run if missing.
