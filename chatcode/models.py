from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModelConfig:
    id: str
    display_name: str
    tools: bool = False


@dataclass
class ProviderConfig:
    id: str
    base_url: str
    api_key: str = "dummy"
    models: dict[str, ModelConfig] = field(default_factory=dict)


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    id: str
    provider_id: str
    model_id: str
    system_prompt: str | None
    messages: list[ChatMessage] = field(default_factory=list)
