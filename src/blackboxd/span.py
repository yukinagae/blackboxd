from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from datetime import datetime, timezone
from typing import Any

from blackboxd.context import build_event, new_span, pop_span, push_span, resolve_storage
from blackboxd.storage.base import Storage


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _TraceSpan(AbstractContextManager, AbstractAsyncContextManager):
    def __init__(
        self,
        name: str,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        storage: Storage | str | None = None,
    ) -> None:
        self.name = name
        self.tags = tags or []
        self.metadata = metadata or {}
        self.storage = resolve_storage(storage)
        self._span = None
        self._token = None
        self._event = None

    def __enter__(self):
        self._span = new_span(self.name, tags=self.tags, metadata=self.metadata)
        self._token = push_span(self._span)
        self._event = build_event(
            kind="span",
            name=self.name,
            span=self._span,
            tags=self.tags,
            metadata=self.metadata,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._event is not None:
            self._event.finish(
                ended_at=utc_now(),
                error=f"{exc_type.__name__}: {exc}" if exc_type and exc else None,
            )
            self.storage.write_event(self._event)
        if self._token is not None:
            pop_span(self._token)
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return self.__exit__(exc_type, exc, tb)


def trace_span(
    name: str,
    *,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    storage: Storage | str | None = None,
) -> _TraceSpan:
    return _TraceSpan(name, tags=tags, metadata=metadata, storage=storage)
