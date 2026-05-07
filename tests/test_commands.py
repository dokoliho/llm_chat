import pytest
from unittest.mock import MagicMock, patch
from chatcode.commands import parse_command, dispatch, CommandContext
from chatcode.models import ChatMessage, ModelConfig, ProviderConfig
from datetime import datetime


def _make_context(**overrides) -> CommandContext:
    providers = {
        "my-prov": ProviderConfig(
            id="my-prov",
            base_url="http://localhost/v1",
            models={"my-model": ModelConfig(id="my-model", display_name="My Model")},
        )
    }
    defaults = dict(
        providers=providers,
        messages=[],
        system_prompt=None,
        current_provider_id="my-prov",
        current_model_id="my-model",
        should_exit=False,
        select_model_interactive=MagicMock(return_value=("my-prov", "my-model")),
        save_session_fn=MagicMock(),
        load_session_fn=MagicMock(),
    )
    defaults.update(overrides)
    return CommandContext(**defaults)


def test_parse_command_simple():
    assert parse_command(":help") == (":help", [])


def test_parse_command_with_two_args():
    assert parse_command(":use proxy-ollama qwen3.5:122b") == (
        ":use", ["proxy-ollama", "qwen3.5:122b"]
    )


def test_parse_command_with_one_arg():
    assert parse_command(":load mysession.json") == (":load", ["mysession.json"])


def test_parse_command_uppercase_normalised():
    cmd, _ = parse_command(":HELP")
    assert cmd == ":help"


def test_clear_removes_messages_keeps_system_prompt():
    ctx = _make_context(
        messages=[ChatMessage(role="user", content="hi", timestamp=datetime.now())],
        system_prompt="Be brief.",
    )
    dispatch(":clear", ctx)
    assert ctx.messages == []
    assert ctx.system_prompt == "Be brief."


def test_system_sets_prompt():
    ctx = _make_context()
    dispatch(":system You are helpful.", ctx)
    assert ctx.system_prompt == "You are helpful."


def test_exit_sets_flag():
    ctx = _make_context()
    dispatch(":exit", ctx)
    assert ctx.should_exit is True


def test_use_with_args_switches_model():
    ctx = _make_context()
    dispatch(":use my-prov my-model", ctx)
    assert ctx.current_provider_id == "my-prov"
    assert ctx.current_model_id == "my-model"


def test_use_without_args_calls_interactive_picker():
    mock_picker = MagicMock(return_value=("my-prov", "my-model"))
    ctx = _make_context(select_model_interactive=mock_picker)
    dispatch(":use", ctx)
    mock_picker.assert_called_once()


def test_unknown_command_does_not_raise():
    ctx = _make_context()
    with patch("chatcode.commands.Console"):
        dispatch(":nonexistent", ctx)
    assert ctx.should_exit is False
