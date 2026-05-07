import json
import pytest
from pathlib import Path
from chatcode.config import load_config, _strip_jsonc_comments


def test_strip_line_comments():
    raw = '{"key": "value"} // this is a comment\n'
    result = _strip_jsonc_comments(raw)
    assert "//" not in result
    assert '"key"' in result


def test_strip_block_comments():
    raw = '/* header */\n{"key": /* inline */ "value"}'
    result = _strip_jsonc_comments(raw)
    assert "/*" not in result
    assert '"key"' in result


def test_load_minimal_config(tmp_path: Path):
    cfg = tmp_path / "opencode.json"
    cfg.write_text(json.dumps({
        "provider": {
            "my-provider": {
                "options": {"baseURL": "http://localhost:11434/v1", "apiKey": "secret"},
                "models": {
                    "my-model": {"displayName": "My Model", "tools": False}
                }
            }
        }
    }))
    providers = load_config(cfg)
    assert "my-provider" in providers
    p = providers["my-provider"]
    assert p.base_url == "http://localhost:11434/v1"
    assert p.api_key == "secret"
    assert "my-model" in p.models
    assert p.models["my-model"].display_name == "My Model"


def test_missing_api_key_defaults_to_dummy(tmp_path: Path):
    cfg = tmp_path / "opencode.json"
    cfg.write_text(json.dumps({
        "provider": {
            "no-key": {
                "options": {"baseURL": "http://localhost/v1"},
                "models": {}
            }
        }
    }))
    providers = load_config(cfg)
    assert providers["no-key"].api_key == "dummy"


def test_missing_display_name_falls_back_to_id(tmp_path: Path):
    cfg = tmp_path / "opencode.json"
    cfg.write_text(json.dumps({
        "provider": {
            "p": {
                "options": {"baseURL": "http://localhost/v1"},
                "models": {"raw-model": {}}
            }
        }
    }))
    providers = load_config(cfg)
    assert providers["p"].models["raw-model"].display_name == "raw-model"


def test_jsonc_with_comments(tmp_path: Path):
    cfg = tmp_path / "opencode.jsonc"
    cfg.write_text(
        '// top comment\n'
        '{\n'
        '  "$schema": "https://opencode.ai/config.json", // inline\n'
        '  "provider": {\n'
        '    /* block */\n'
        '    "p": {\n'
        '      "options": {"baseURL": "http://localhost/v1"},\n'
        '      "models": {}\n'
        '    }\n'
        '  }\n'
        '}\n'
    )
    providers = load_config(cfg)
    assert "p" in providers


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_config(tmp_path / "nonexistent.json")


def test_invalid_json_raises(tmp_path: Path):
    cfg = tmp_path / "bad.json"
    cfg.write_text("{not valid json}")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config(cfg)
