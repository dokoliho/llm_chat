from __future__ import annotations

import json
import re
from pathlib import Path

from chatcode.models import ModelConfig, ProviderConfig

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "opencode" / "opencode.json"


def _strip_jsonc_comments(text: str) -> str:
    """Remove // line comments and /* block comments */ from JSONC text,
    while leaving comment-like sequences inside string literals untouched."""
    result: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # Inside a JSON string — copy verbatim until closing unescaped quote
        if ch == '"':
            result.append(ch)
            i += 1
            while i < n:
                c = text[i]
                result.append(c)
                if c == '\\':
                    # Escaped character — consume the next char too
                    i += 1
                    if i < n:
                        result.append(text[i])
                elif c == '"':
                    break
                i += 1
            i += 1
        # Line comment
        elif ch == '/' and i + 1 < n and text[i + 1] == '/':
            while i < n and text[i] != '\n':
                i += 1
        # Block comment
        elif ch == '/' and i + 1 < n and text[i + 1] == '*':
            i += 2
            while i < n:
                if text[i] == '*' and i + 1 < n and text[i + 1] == '/':
                    i += 2
                    break
                i += 1
        else:
            result.append(ch)
            i += 1
    return "".join(result)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, ProviderConfig]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(_strip_jsonc_comments(raw))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file {path}: {exc}") from exc

    providers: dict[str, ProviderConfig] = {}
    for provider_id, provider_data in data.get("provider", {}).items():
        options = provider_data.get("options", {})
        models: dict[str, ModelConfig] = {}
        for model_id, model_data in provider_data.get("models", {}).items():
            models[model_id] = ModelConfig(
                id=model_id,
                display_name=model_data.get("displayName", model_id),
                tools=model_data.get("tools", False),
            )
        providers[provider_id] = ProviderConfig(
            id=provider_id,
            base_url=options.get("baseURL", ""),
            api_key=options.get("apiKey", "dummy"),
            models=models,
        )
    return providers
