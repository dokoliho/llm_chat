from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from chatcode.models import ChatMessage, Session

SESSIONS_DIR = Path.home() / ".config" / "chatcode" / "sessions"


def make_session_id() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def save_session(session: Session, filename: str | None = None) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    name = filename or f"{session.id}.json"
    if not name.endswith((".json", ".md")):
        name += ".json"
    path = SESSIONS_DIR / name
    if name.endswith(".md"):
        path.write_text(_to_markdown(session), encoding="utf-8")
    else:
        path.write_text(_to_json(session), encoding="utf-8")
    return path


def load_session(filename: str) -> Session:
    path = SESSIONS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Session nicht gefunden: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    messages = [
        ChatMessage(
            role=m["role"],
            content=m["content"],
            timestamp=datetime.fromisoformat(m["timestamp"]),
        )
        for m in data.get("messages", [])
    ]
    return Session(
        id=data["id"],
        provider_id=data["provider"],
        model_id=data["model"],
        system_prompt=data.get("system_prompt"),
        messages=messages,
    )


def _to_json(session: Session) -> str:
    return json.dumps(
        {
            "id": session.id,
            "provider": session.provider_id,
            "model": session.model_id,
            "system_prompt": session.system_prompt,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in session.messages
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def _to_markdown(session: Session) -> str:
    lines = [
        f"# Session: {session.id}",
        f"Provider: {session.provider_id} / {session.model_id}",
        "",
    ]
    if session.system_prompt:
        lines += [f"**System:** {session.system_prompt}", ""]
    for m in session.messages:
        heading = "## User" if m.role == "user" else "## Assistant"
        lines += [heading, m.content, ""]
    return "\n".join(lines)
