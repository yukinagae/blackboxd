from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from blackboxd.config import get_config
from blackboxd.models import TraceEvent
from blackboxd.serialization import to_jsonable
from blackboxd.storage.base import Storage
from blackboxd.storage.jsonl import JSONLStorage


@dataclass(slots=True)
class ActiveSpan:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


_SPAN_STACK: ContextVar[list[ActiveSpan]] = ContextVar("blackboxd_span_stack", default=[])


def current_span() -> ActiveSpan | None:
    stack = _SPAN_STACK.get()
    return stack[-1] if stack else None


def push_span(span: ActiveSpan):
    stack = list(_SPAN_STACK.get())
    stack.append(span)
    return _SPAN_STACK.set(stack)


def pop_span(token) -> None:
    _SPAN_STACK.reset(token)


def resolve_storage(storage: Storage | str | None) -> Storage:
    if isinstance(storage, Storage):
        return storage
    if isinstance(storage, str):
        return JSONLStorage(storage)
    return get_config().storage


def new_span(name: str, *, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> ActiveSpan:
    parent = current_span()
    trace_id = parent.trace_id if parent else str(uuid4())
    return ActiveSpan(
        trace_id=trace_id,
        span_id=str(uuid4()),
        parent_span_id=parent.span_id if parent else None,
        name=name,
        tags=list(tags or []),
        metadata=dict(metadata or {}),
    )


def build_event(
    *,
    kind: str,
    name: str,
    span: ActiveSpan,
    event_type: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    input_data: Any = None,
    output_data: Any = None,
    prompt: Any = None,
    response: Any = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> TraceEvent:
    config = get_config()
    merged_tags = [*config.default_tags, *span.tags, *(tags or [])]
    merged_metadata = {
        **config.default_metadata,
        **span.metadata,
        **(metadata or {}),
    }
    return TraceEvent(
        kind=kind,
        name=name,
        trace_id=span.trace_id,
        span_id=span.span_id,
        parent_span_id=span.parent_span_id,
        provider=provider,
        model=model,
        prompt=to_jsonable(input_data if input_data is not None else prompt),
        response=to_jsonable(output_data if output_data is not None else response),
        tags=merged_tags,
        metadata=to_jsonable(merged_metadata),
        environment=config.environment,
        app_version=config.app_version,
    )
