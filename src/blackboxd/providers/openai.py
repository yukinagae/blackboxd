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
        input_tokens=getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None),
    )


class _ResponsesAPI:
    def __init__(self, client: Any, *, provider: str, storage: Storage | str | None) -> None:
        self._client = client
        self._provider = provider
        self._storage = storage

    def create(self, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = self._client.responses.create(**kwargs)
        except Exception as exc:
            capture_llm_call(
                name="openai.responses.create",
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
            name="openai.responses.create",
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


class _AsyncResponsesAPI(_ResponsesAPI):
    async def create(self, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = await self._client.responses.create(**kwargs)
        except Exception as exc:
            capture_llm_call(
                name="openai.responses.create",
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
            name="openai.responses.create",
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


class _ChatCompletionsAPI:
    def __init__(self, client: Any, *, provider: str, storage: Storage | str | None) -> None:
        self._client = client
        self._provider = provider
        self._storage = storage

    def create(self, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            capture_llm_call(
                name="openai.chat.completions.create",
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
            name="openai.chat.completions.create",
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


class _AsyncChatCompletionsAPI(_ChatCompletionsAPI):
    async def create(self, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = await self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            capture_llm_call(
                name="openai.chat.completions.create",
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
            name="openai.chat.completions.create",
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


class _ChatAPI:
    def __init__(self, client: Any, *, provider: str, storage: Storage | str | None, async_mode: bool) -> None:
        completion_cls = _AsyncChatCompletionsAPI if async_mode else _ChatCompletionsAPI
        self.completions = completion_cls(client, provider=provider, storage=storage)


class _BaseOpenAIWrapper:
    def __init__(self, client: Any, *, provider: str = "openai", storage: Storage | str | None = None) -> None:
        self._client = client
        self._storage = storage
        self.responses = self._responses_cls(client, provider=provider, storage=storage)
        self.chat = _ChatAPI(client, provider=provider, storage=storage, async_mode=self._async_mode)

    def __getattr__(self, item: str) -> Any:
        return getattr(self._client, item)


class OpenAI(_BaseOpenAIWrapper):
    _responses_cls = _ResponsesAPI
    _async_mode = False

    def __init__(self, *args, storage: Storage | str | None = None, **kwargs) -> None:
        try:
            from openai import OpenAI as SDKOpenAI
        except ImportError as exc:
            raise RuntimeError("openai is required. Install blackboxd[openai].") from exc
        super().__init__(SDKOpenAI(*args, **kwargs), storage=storage)


class AsyncOpenAI(_BaseOpenAIWrapper):
    _responses_cls = _AsyncResponsesAPI
    _async_mode = True

    def __init__(self, *args, storage: Storage | str | None = None, **kwargs) -> None:
        try:
            from openai import AsyncOpenAI as SDKAsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai is required. Install blackboxd[openai].") from exc
        super().__init__(SDKAsyncOpenAI(*args, **kwargs), storage=storage)
