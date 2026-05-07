import json
import pytest
from pathlib import Path
from unittest.mock import patch
from chatcode.state import load_last_used, save_last_used


def test_save_and_load(tmp_path: Path):
    state_file = tmp_path / "state.json"
    with patch("chatcode.state.STATE_PATH", state_file):
        save_last_used("proxy-ollama", "qwen3.5:122b")
        result = load_last_used()
    assert result == ("proxy-ollama", "qwen3.5:122b")


def test_load_missing_file_returns_none(tmp_path: Path):
    state_file = tmp_path / "nonexistent.json"
    with patch("chatcode.state.STATE_PATH", state_file):
        result = load_last_used()
    assert result is None


def test_load_corrupt_file_returns_none(tmp_path: Path):
    state_file = tmp_path / "state.json"
    state_file.write_text("not json")
    with patch("chatcode.state.STATE_PATH", state_file):
        result = load_last_used()
    assert result is None


def test_save_creates_parent_dirs(tmp_path: Path):
    state_file = tmp_path / "nested" / "dir" / "state.json"
    with patch("chatcode.state.STATE_PATH", state_file):
        save_last_used("prov", "mod")
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data == {"last_provider": "prov", "last_model": "mod"}
