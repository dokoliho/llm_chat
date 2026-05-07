import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from chatcode.models import ChatMessage, Session
from chatcode.session import save_session, load_session, make_session_id


def _make_session() -> Session:
    return Session(
        id="2026-05-07T14-00-00",
        provider_id="proxy-ollama",
        model_id="qwen3.5:122b",
        system_prompt="Be concise.",
        messages=[
            ChatMessage(role="user", content="Hello", timestamp=datetime(2026, 5, 7, 14, 0, 0)),
            ChatMessage(role="assistant", content="Hi!", timestamp=datetime(2026, 5, 7, 14, 0, 1)),
        ],
    )


def test_save_and_load_json(tmp_path: Path):
    session = _make_session()
    with patch("chatcode.session.SESSIONS_DIR", tmp_path):
        path = save_session(session)
        loaded = load_session(path.name)

    assert loaded.id == session.id
    assert loaded.provider_id == session.provider_id
    assert loaded.model_id == session.model_id
    assert loaded.system_prompt == session.system_prompt
    assert len(loaded.messages) == 2
    assert loaded.messages[0].role == "user"
    assert loaded.messages[0].content == "Hello"


def test_save_creates_json_by_default(tmp_path: Path):
    session = _make_session()
    with patch("chatcode.session.SESSIONS_DIR", tmp_path):
        path = save_session(session)
    assert path.suffix == ".json"


def test_save_markdown(tmp_path: Path):
    session = _make_session()
    with patch("chatcode.session.SESSIONS_DIR", tmp_path):
        path = save_session(session, "my-session.md")
    content = path.read_text(encoding="utf-8")
    assert "## User" in content
    assert "Hello" in content
    assert "## Assistant" in content
    assert "Hi!" in content


def test_load_missing_raises(tmp_path: Path):
    with patch("chatcode.session.SESSIONS_DIR", tmp_path):
        with pytest.raises(FileNotFoundError, match="Session nicht gefunden"):
            load_session("nope.json")


def test_make_session_id_format():
    sid = make_session_id()
    # format: YYYY-MM-DDTHH-MM-SS
    assert len(sid) == 19
    assert sid[4] == "-"
    assert sid[7] == "-"
    assert sid[10] == "T"


def test_custom_filename_gets_json_extension(tmp_path: Path):
    session = _make_session()
    with patch("chatcode.session.SESSIONS_DIR", tmp_path):
        path = save_session(session, "myfile")
    assert path.name == "myfile.json"
