from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from blackboxd.span import trace_span
from blackboxd.storage.base import Storage


def trace_llm(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    storage: Storage | str | None = None,
):
    def decorator(target: Callable[..., Any]):
        span_name = name or target.__name__

        if inspect.iscoroutinefunction(target):

            @wraps(target)
            async def async_wrapper(*args, **kwargs):
                async with trace_span(
                    span_name,
                    tags=tags,
                    metadata=metadata,
                    storage=storage,
                ):
                    return await target(*args, **kwargs)

            return async_wrapper

        @wraps(target)
        def sync_wrapper(*args, **kwargs):
            with trace_span(
                span_name,
                tags=tags,
                metadata=metadata,
                storage=storage,
            ):
                return target(*args, **kwargs)

        return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator
