from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from blackboxd.context import build_event, current_span, new_span, resolve_storage
from blackboxd.models import TokenUsage
from blackboxd.serialization import to_jsonable
from blackboxd.storage.base import Storage


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def capture_llm_call(
    *,
    name: str,
    provider: str,
    model: str | None,
    prompt: Any,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    response: Any = None,
    error: Exception | None = None,
    usage: TokenUsage | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    storage: Storage | str | None = None,
) -> None:
    active = current_span()
    synthetic_span = active or new_span(name)
    llm_span_id = str(uuid4())
    event = build_event(
        kind="llm",
        name=name,
        span=synthetic_span,
        provider=provider,
        model=model,
        prompt=prompt,
        response=response,
        tags=tags,
        metadata=metadata,
    )
    event.span_id = llm_span_id
    event.parent_span_id = active.span_id if active else synthetic_span.parent_span_id
    event.created_at = started_at or utc_now()
    event.finish(
        ended_at=ended_at or utc_now(),
        response=to_jsonable(response),
        error=f"{type(error).__name__}: {error}" if error else None,
    )
    event.apply_usage(usage)
    resolve_storage(storage).write_event(event)
