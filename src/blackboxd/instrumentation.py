from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import inspect
from typing import Any, Callable

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


def _wrap_call(
    *,
    callable_obj: Callable[..., Any],
    event_name: str,
    provider: str,
    storage: Storage | str | None,
):
    def wrapped(*args, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = callable_obj(*args, **kwargs)
        except Exception as exc:
            capture_llm_call(
                name=event_name,
                provider=provider,
                model=model,
                prompt=kwargs,
                started_at=started_at,
                ended_at=_utc_now(),
                error=exc,
                storage=storage,
            )
            raise
        capture_llm_call(
            name=event_name,
            provider=provider,
            model=model,
            prompt=kwargs,
            started_at=started_at,
            ended_at=_utc_now(),
            response=response,
            usage=_extract_usage(response),
            storage=storage,
        )
        return response

    return wrapped


def _wrap_async_call(
    *,
    callable_obj: Callable[..., Any],
    event_name: str,
    provider: str,
    storage: Storage | str | None,
):
    async def wrapped(*args, **kwargs):
        model = kwargs.get("model")
        started_at = _utc_now()
        try:
            response = await callable_obj(*args, **kwargs)
        except Exception as exc:
            capture_llm_call(
                name=event_name,
                provider=provider,
                model=model,
                prompt=kwargs,
                started_at=started_at,
                ended_at=_utc_now(),
                error=exc,
                storage=storage,
            )
            raise
        capture_llm_call(
            name=event_name,
            provider=provider,
            model=model,
            prompt=kwargs,
            started_at=started_at,
            ended_at=_utc_now(),
            response=response,
            usage=_extract_usage(response),
            storage=storage,
        )
        return response

    return wrapped


def instrument_openai(client: Any, *, storage: Storage | str | None = None) -> Any:
    if getattr(client, "_blackboxd_instrumented", False):
        return client

    if hasattr(client, "responses") and hasattr(client.responses, "create"):
        create = client.responses.create
        if callable(create):
            client.responses.create = (
                _wrap_async_call(
                    callable_obj=create,
                    event_name="openai.responses.create",
                    provider="openai",
                    storage=storage,
                )
                if inspect.iscoroutinefunction(create)
                else _wrap_call(
                    callable_obj=create,
                    event_name="openai.responses.create",
                    provider="openai",
                    storage=storage,
                )
            )

    if hasattr(client, "chat") and hasattr(client.chat, "completions") and hasattr(client.chat.completions, "create"):
        create = client.chat.completions.create
        if callable(create):
            client.chat.completions.create = (
                _wrap_async_call(
                    callable_obj=create,
                    event_name="openai.chat.completions.create",
                    provider="openai",
                    storage=storage,
                )
                if inspect.iscoroutinefunction(create)
                else _wrap_call(
                    callable_obj=create,
                    event_name="openai.chat.completions.create",
                    provider="openai",
                    storage=storage,
                )
            )

    client._blackboxd_instrumented = True
    return client


def instrument_anthropic(client: Any, *, storage: Storage | str | None = None) -> Any:
    if getattr(client, "_blackboxd_instrumented", False):
        return client

    if hasattr(client, "messages") and hasattr(client.messages, "create"):
        create = client.messages.create
        if callable(create):
            client.messages.create = (
                _wrap_async_call(
                    callable_obj=create,
                    event_name="anthropic.messages.create",
                    provider="anthropic",
                    storage=storage,
                )
                if inspect.iscoroutinefunction(create)
                else _wrap_call(
                    callable_obj=create,
                    event_name="anthropic.messages.create",
                    provider="anthropic",
                    storage=storage,
                )
            )

    client._blackboxd_instrumented = True
    return client


@dataclass(slots=True)
class PatchHandle:
    target: Any
    attribute: str
    original: Any

    def restore(self) -> None:
        setattr(self.target, self.attribute, self.original)


def patch_openai(client: Any, *, storage: Storage | str | None = None) -> list[PatchHandle]:
    handles: list[PatchHandle] = []
    if hasattr(client, "responses") and hasattr(client.responses, "create"):
        original = client.responses.create
        client.responses.create = (
            _wrap_async_call(
                callable_obj=original,
                event_name="openai.responses.create",
                provider="openai",
                storage=storage,
            )
            if inspect.iscoroutinefunction(original)
            else _wrap_call(
                callable_obj=original,
                event_name="openai.responses.create",
                provider="openai",
                storage=storage,
            )
        )
        handles.append(PatchHandle(client.responses, "create", original))
    if hasattr(client, "chat") and hasattr(client.chat, "completions") and hasattr(client.chat.completions, "create"):
        original = client.chat.completions.create
        client.chat.completions.create = (
            _wrap_async_call(
                callable_obj=original,
                event_name="openai.chat.completions.create",
                provider="openai",
                storage=storage,
            )
            if inspect.iscoroutinefunction(original)
            else _wrap_call(
                callable_obj=original,
                event_name="openai.chat.completions.create",
                provider="openai",
                storage=storage,
            )
        )
        handles.append(PatchHandle(client.chat.completions, "create", original))
    return handles


def patch_anthropic(client: Any, *, storage: Storage | str | None = None) -> list[PatchHandle]:
    handles: list[PatchHandle] = []
    if hasattr(client, "messages") and hasattr(client.messages, "create"):
        original = client.messages.create
        client.messages.create = (
            _wrap_async_call(
                callable_obj=original,
                event_name="anthropic.messages.create",
                provider="anthropic",
                storage=storage,
            )
            if inspect.iscoroutinefunction(original)
            else _wrap_call(
                callable_obj=original,
                event_name="anthropic.messages.create",
                provider="anthropic",
                storage=storage,
            )
        )
        handles.append(PatchHandle(client.messages, "create", original))
    return handles
