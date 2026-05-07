from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path.home() / ".config" / "chatcode" / "state.json"


def load_last_used() -> tuple[str, str] | None:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        provider = data.get("last_provider")
        model = data.get("last_model")
        if provider and model:
            return provider, model
        return None
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save_last_used(provider_id: str, model_id: str) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps({"last_provider": provider_id, "last_model": model_id}),
        encoding="utf-8",
    )
