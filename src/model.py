"""Model router supporting multiple AI providers with fallback."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator

from src.settings import Settings

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"
    GOOGLE = "google"
    LOCAL = "local"


@dataclass
class Message:
    role: str  # system | user | assistant | tool
    content: str | list[dict[str, Any]]
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class ModelResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        ...

    async def stream(
        self,
        messages: list[Message],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Optional streaming. Default falls back to full response."""
        resp = await self.chat(messages, model, **kwargs)
        yield resp.content


class OpenAICompatibleProvider(BaseProvider):
    """Works for OpenAI, xAI, local Ollama/LM Studio, etc."""

    def __init__(self, api_key: str | None, base_url: str | None = None, name: str = "openai"):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key or "sk-local",
                base_url=self.base_url,
            )
        return self._client

    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        client = self._get_client()
        payload = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        create_kwargs: dict[str, Any] = {
            "model": model,
            "messages": payload,
            "temperature": temperature,
        }
        if max_tokens:
            create_kwargs["max_tokens"] = max_tokens
        if tools:
            create_kwargs["tools"] = tools

        resp = await client.chat.completions.create(**create_kwargs)
        choice = resp.choices[0]
        content = choice.message.content or ""
        usage = {}
        if resp.usage:
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens or 0,
                "completion_tokens": resp.usage.completion_tokens or 0,
            }
        return ModelResponse(
            content=content,
            model=resp.model or model,
            provider=self.name,
            usage=usage,
            raw=resp,
        )


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        client = self._get_client()
        system = ""
        conv = []
        for m in messages:
            if m.role == "system":
                system = m.content if isinstance(m.content, str) else str(m.content)
            else:
                conv.append({"role": m.role, "content": m.content})

        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            system=system or None,
            messages=conv,
        )
        content = ""
        for block in resp.content:
            if hasattr(block, "text"):
                content += block.text
        return ModelResponse(
            content=content,
            model=resp.model,
            provider=self.name,
            usage={
                "prompt_tokens": resp.usage.input_tokens,
                "completion_tokens": resp.usage.output_tokens,
            },
            raw=resp,
        )


def parse_model_spec(spec: str) -> tuple[str, str]:
    """'openai:gpt-4o' -> ('openai', 'gpt-4o')"""
    if ":" in spec:
        provider, model = spec.split(":", 1)
        return provider.strip().lower(), model.strip()
    return "openai", spec.strip()


class ModelRouter:
    """Routes requests to the appropriate provider with fallback."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.providers: dict[str, BaseProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        s = self.settings
        if s.openai_api_key:
            self.providers["openai"] = OpenAICompatibleProvider(
                s.openai_api_key, name="openai"
            )
        if s.xai_api_key:
            self.providers["xai"] = OpenAICompatibleProvider(
                s.xai_api_key,
                base_url="https://api.x.ai/v1",
                name="xai",
            )
        if s.anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(s.anthropic_api_key)
        if s.local_api_base:
            self.providers["local"] = OpenAICompatibleProvider(
                s.local_api_key,
                base_url=s.local_api_base,
                name="local",
            )

    def list_available(self) -> list[str]:
        return list(self.providers.keys())

    def current_model_name(self) -> str:
        return self.settings.primary_model

    async def chat(
        self,
        messages: list[Message],
        model_spec: str | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        spec = model_spec or self.settings.primary_model
        provider_name, model = parse_model_spec(spec)
        temp = temperature if temperature is not None else self.settings.ai.temperature

        chain = [spec]
        if self.settings.fallback_models:
            chain.extend(
                m.strip() for m in self.settings.fallback_models.split(",") if m.strip()
            )

        last_error: Exception | None = None
        for candidate in chain:
            p_name, m_name = parse_model_spec(candidate)
            provider = self.providers.get(p_name)
            if not provider:
                logger.warning("Provider %s not configured, skipping", p_name)
                continue
            try:
                logger.info("Trying %s / %s", p_name, m_name)
                return await provider.chat(
                    messages, m_name, temperature=temp, **kwargs
                )
            except Exception as e:
                logger.exception("Provider %s failed: %s", p_name, e)
                last_error = e

        raise RuntimeError(
            f"No available AI model. Last error: {last_error}"
        ) from last_error
