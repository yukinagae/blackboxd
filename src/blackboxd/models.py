from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(slots=True)
class TraceEvent:
    name: str
    trace_id: str
    span_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    kind: Literal["span", "io", "llm"] = "span"
    created_at: datetime = field(default_factory=utc_now)
    ended_at: datetime | None = None
    latency_ms: int | None = None
    parent_span_id: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt: Any = None
    response: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None
    environment: str | None = None
    app_version: str | None = None

    def finish(self, *, ended_at: datetime, response: Any = None, error: str | None = None) -> None:
        self.ended_at = ended_at
        self.latency_ms = int((ended_at - self.created_at).total_seconds() * 1000)
        if response is not None:
            self.response = response
        if error is not None:
            self.error = error

    def apply_usage(self, usage: TokenUsage | None) -> None:
        if usage is None:
            return
        self.input_tokens = usage.input_tokens
        self.output_tokens = usage.output_tokens

    def model_dump(self, *, mode: str = "python") -> dict[str, Any]:
        payload = asdict(self)
        payload["event_type"] = self.kind
        payload["input"] = payload["prompt"]
        payload["output"] = payload["response"]
        if mode == "json":
            from blackboxd.serialization import to_jsonable

            return to_jsonable(payload)
        return payload
