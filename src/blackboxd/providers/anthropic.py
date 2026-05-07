from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from blackboxd.capture import capture_llm_call
from blackboxd.models import TokenUsage
from blackboxd.storage.base import Storage


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _extract_usage(response: Any) -> TokenUsage | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    return TokenUsage(
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
    )


class _MessagesAPI:
    def __init__(self, client: Any, *, provider: str, storage: Storage | str | None) -> None:
        self._client = client
        self._provider = provider
        self._storage = storage

    def create(self, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = self._client.messages.create(**kwargs)
        except Exception as exc:
            capture_llm_call(
                name="anthropic.messages.create",
                provider=self._provider,
                model=model,
                prompt=kwargs,
                started_at=started_at,
                ended_at=_utc_now(),
                error=exc,
                storage=self._storage,
            )
            raise
        capture_llm_call(
            name="anthropic.messages.create",
            provider=self._provider,
            model=model,
            prompt=kwargs,
            started_at=started_at,
            ended_at=_utc_now(),
            response=response,
            usage=_extract_usage(response),
            storage=self._storage,
        )
        return response


class _AsyncMessagesAPI(_MessagesAPI):
    async def create(self, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = await self._client.messages.create(**kwargs)
        except Exception as exc:
            capture_llm_call(
                name="anthropic.messages.create",
                provider=self._provider,
                model=model,
                prompt=kwargs,
                started_at=started_at,
                ended_at=_utc_now(),
                error=exc,
                storage=self._storage,
            )
            raise
        capture_llm_call(
            name="anthropic.messages.create",
            provider=self._provider,
            model=model,
            prompt=kwargs,
            started_at=started_at,
            ended_at=_utc_now(),
            response=response,
            usage=_extract_usage(response),
            storage=self._storage,
        )
        return response


class _BaseAnthropicWrapper:
    def __init__(self, client: Any, *, provider: str = "anthropic", storage: Storage | str | None = None) -> None:
        self._client = client
        self.messages = self._messages_cls(client, provider=provider, storage=storage)

    def __getattr__(self, item: str) -> Any:
        return getattr(self._client, item)


class Anthropic(_BaseAnthropicWrapper):
    _messages_cls = _MessagesAPI

    def __init__(self, *args, storage: Storage | str | None = None, **kwargs) -> None:
        try:
            from anthropic import Anthropic as SDKAnthropic
        except ImportError as exc:
            raise RuntimeError("anthropic is required. Install blackboxd[anthropic].") from exc
        super().__init__(SDKAnthropic(*args, **kwargs), storage=storage)


class AsyncAnthropic(_BaseAnthropicWrapper):
    _messages_cls = _AsyncMessagesAPI

    def __init__(self, *args, storage: Storage | str | None = None, **kwargs) -> None:
        try:
            from anthropic import AsyncAnthropic as SDKAsyncAnthropic
        except ImportError as exc:
            raise RuntimeError("anthropic is required. Install blackboxd[anthropic].") from exc
        super().__init__(SDKAsyncAnthropic(*args, **kwargs), storage=storage)
