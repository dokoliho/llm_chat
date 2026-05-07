from __future__ import annotations

from collections.abc import Callable

import openai

from chatcode.models import ChatMessage, ProviderConfig


def make_client(provider: ProviderConfig) -> openai.OpenAI:
    return openai.OpenAI(base_url=provider.base_url, api_key=provider.api_key)


def stream_chat(
    client: openai.OpenAI,
    model_id: str,
    messages: list[ChatMessage],
    system_prompt: str | None,
    on_token: Callable[[str], None],
) -> str:
    api_messages: list[dict] = []
    if system_prompt:
        api_messages.append({"role": "system", "content": system_prompt})
    api_messages.extend({"role": m.role, "content": m.content} for m in messages)

    full_text = ""
    try:
        stream = client.chat.completions.create(
            model=model_id,
            messages=api_messages,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content or ""
            if token:
                on_token(token)
                full_text += token
    except openai.APITimeoutError as exc:
        raise TimeoutError("Timeout — Server antwortet nicht") from exc
    except openai.APIConnectionError as exc:
        raise ConnectionError(f"Verbindung fehlgeschlagen: {exc}") from exc
    except openai.APIStatusError as exc:
        raise RuntimeError(f"API-Fehler {exc.status_code}: {exc.message}") from exc

    return full_text
