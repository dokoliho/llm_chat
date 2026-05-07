import pytest
from unittest.mock import MagicMock, patch
import openai
from chatcode.client import make_client, stream_chat
from chatcode.models import ChatMessage, ProviderConfig
from datetime import datetime


def _provider() -> ProviderConfig:
    return ProviderConfig(id="test", base_url="http://localhost/v1", api_key="key")


def _msg(role: str, content: str) -> ChatMessage:
    return ChatMessage(role=role, content=content, timestamp=datetime.now())


def _make_chunk(content: str | None) -> MagicMock:
    chunk = MagicMock()
    chunk.choices[0].delta.content = content
    return chunk


def test_make_client_uses_provider_settings():
    with patch("chatcode.client.openai.OpenAI") as mock_cls:
        make_client(_provider())
    mock_cls.assert_called_once_with(base_url="http://localhost/v1", api_key="key")


def test_stream_chat_returns_full_text():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = iter([
        _make_chunk("Hello"),
        _make_chunk(" world"),
        _make_chunk(None),
    ])
    tokens: list[str] = []
    result = stream_chat(mock_client, "test-model", [_msg("user", "hi")], None, tokens.append)
    assert result == "Hello world"
    assert tokens == ["Hello", " world"]


def test_stream_chat_includes_system_prompt():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = iter([_make_chunk("ok")])
    stream_chat(mock_client, "m", [_msg("user", "hi")], "Be brief.", lambda t: None)
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "Be brief."}
    assert messages[1] == {"role": "user", "content": "hi"}


def test_stream_chat_connection_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = openai.APIConnectionError(
        message="refused", request=MagicMock()
    )
    with pytest.raises(ConnectionError, match="Verbindung fehlgeschlagen"):
        stream_chat(mock_client, "m", [], None, lambda t: None)


def test_stream_chat_status_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = openai.APIStatusError(
        "Not found", response=MagicMock(status_code=404), body=None
    )
    with pytest.raises(RuntimeError, match="API-Fehler 404"):
        stream_chat(mock_client, "m", [], None, lambda t: None)


def test_stream_chat_timeout_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
        request=MagicMock()
    )
    with pytest.raises(TimeoutError, match="Timeout"):
        stream_chat(mock_client, "m", [], None, lambda t: None)
