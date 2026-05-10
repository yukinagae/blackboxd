from __future__ import annotations

import inspect
from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
from typing import Any
from uuid import uuid4

from blackboxd.context import build_event, current_span, new_span, resolve_storage
from blackboxd.serialization import to_jsonable
from blackboxd.storage.base import Storage


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def record_io(
    *,
    name: str,
    input_data: Any = None,
    output_data: Any = None,
    error: Exception | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    storage: Storage | str | None = None,
) -> None:
    active = current_span()
    synthetic_span = active or new_span(name, tags=tags, metadata=metadata)
    event = build_event(
        kind="io",
        name=name,
        span=synthetic_span,
        input_data=input_data,
        output_data=output_data,
        tags=tags,
        metadata=metadata,
    )
    event.span_id = str(uuid4())
    event.parent_span_id = active.span_id if active else synthetic_span.parent_span_id
    event.created_at = started_at or utc_now()
    event.finish(
        ended_at=ended_at or utc_now(),
        response=to_jsonable(output_data),
        error=f"{type(error).__name__}: {error}" if error else None,
    )
    resolve_storage(storage).write_event(event)


def run_io(
    name: str,
    func: Callable[..., Any],
    *,
    input_data: Any = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    storage: Storage | str | None = None,
):
    started_at = utc_now()
    try:
        output_data = func()
    except Exception as exc:
        record_io(
            name=name,
            input_data=input_data,
            error=exc,
            started_at=started_at,
            ended_at=utc_now(),
            tags=tags,
            metadata=metadata,
            storage=storage,
        )
        raise
    record_io(
        name=name,
        input_data=input_data,
        output_data=output_data,
        started_at=started_at,
        ended_at=utc_now(),
        tags=tags,
        metadata=metadata,
        storage=storage,
    )
    return output_data


async def run_io_async(
    name: str,
    func: Callable[..., Any],
    *,
    input_data: Any = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    storage: Storage | str | None = None,
):
    started_at = utc_now()
    try:
        output_data = await func()
    except Exception as exc:
        record_io(
            name=name,
            input_data=input_data,
            error=exc,
            started_at=started_at,
            ended_at=utc_now(),
            tags=tags,
            metadata=metadata,
            storage=storage,
        )
        raise
    record_io(
        name=name,
        input_data=input_data,
        output_data=output_data,
        started_at=started_at,
        ended_at=utc_now(),
        tags=tags,
        metadata=metadata,
        storage=storage,
    )
    return output_data


def wrap_io_call(
    func: Callable[..., Any],
    *,
    name: str | None = None,
    input_mapper: Callable[..., Any] | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    storage: Storage | str | None = None,
):
    operation_name = name or getattr(func, "__name__", "anonymous")

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            input_data = input_mapper(*args, **kwargs) if input_mapper else {
                "args": args,
                "kwargs": kwargs,
            }
            return await run_io_async(
                operation_name,
                lambda: func(*args, **kwargs),
                input_data=input_data,
                tags=tags,
                metadata=metadata,
                storage=storage,
            )

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        input_data = input_mapper(*args, **kwargs) if input_mapper else {
            "args": args,
            "kwargs": kwargs,
        }
        return run_io(
            operation_name,
            lambda: func(*args, **kwargs),
            input_data=input_data,
            tags=tags,
            metadata=metadata,
            storage=storage,
        )

    return sync_wrapper
