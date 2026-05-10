from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from blackboxd.capture import capture_llm_call
from blackboxd.models import TokenUsage
from blackboxd.serialization import to_jsonable
from blackboxd.storage.base import Storage


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _extract_provider(request: Any) -> str:
    host = getattr(getattr(request, "url", None), "host", "") or ""
    if "anthropic" in host:
        return "anthropic"
    if "openai" in host:
        return "openai"
    return "http"


def _extract_model(payload: Any) -> str | None:
    if isinstance(payload, dict):
        model = payload.get("model")
        return model if isinstance(model, str) else None
    return None


def _extract_usage_from_json(payload: Any) -> TokenUsage | None:
    if not isinstance(payload, dict):
        return None
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    return TokenUsage(
        input_tokens=usage.get("input_tokens") or usage.get("prompt_tokens"),
        output_tokens=usage.get("output_tokens") or usage.get("completion_tokens"),
    )


def _read_request_payload(request: Any) -> Any:
    content = getattr(request, "content", None)
    if isinstance(content, (bytes, bytearray)):
        try:
            import json

            return json.loads(content.decode("utf-8"))
        except Exception:
            return content.decode("utf-8", errors="replace")
    return None


def _read_response_payload(response: Any) -> Any:
    try:
        return response.json()
    except Exception:
        text = getattr(response, "text", None)
        return text if isinstance(text, str) else None


@dataclass(slots=True)
class BlackboxdTransport:
    wrapped: Any
    storage: Storage | str | None = None
    provider: str | None = None

    def handle_request(self, request: Any) -> Any:
        started_at = _utc_now()
        prompt = _read_request_payload(request)
        try:
            response = self.wrapped.handle_request(request)
        except Exception as exc:
            capture_llm_call(
                name=f"{self.provider or _extract_provider(request)}.http",
                provider=self.provider or _extract_provider(request),
                model=_extract_model(prompt),
                prompt=prompt,
                started_at=started_at,
                ended_at=_utc_now(),
                error=exc,
                storage=self.storage,
            )
            raise
        payload = _read_response_payload(response)
        capture_llm_call(
            name=f"{self.provider or _extract_provider(request)}.http",
            provider=self.provider or _extract_provider(request),
            model=_extract_model(prompt),
            prompt=prompt,
            response=payload,
            usage=_extract_usage_from_json(payload),
            started_at=started_at,
            ended_at=_utc_now(),
            storage=self.storage,
        )
        return response

    def close(self) -> None:
        if hasattr(self.wrapped, "close"):
            self.wrapped.close()


@dataclass(slots=True)
class AsyncBlackboxdTransport:
    wrapped: Any
    storage: Storage | str | None = None
    provider: str | None = None

    async def handle_async_request(self, request: Any) -> Any:
        started_at = _utc_now()
        prompt = _read_request_payload(request)
        try:
            response = await self.wrapped.handle_async_request(request)
        except Exception as exc:
            capture_llm_call(
                name=f"{self.provider or _extract_provider(request)}.http",
                provider=self.provider or _extract_provider(request),
                model=_extract_model(prompt),
                prompt=prompt,
                started_at=started_at,
                ended_at=_utc_now(),
                error=exc,
                storage=self.storage,
            )
            raise
        payload = _read_response_payload(response)
        capture_llm_call(
            name=f"{self.provider or _extract_provider(request)}.http",
            provider=self.provider or _extract_provider(request),
            model=_extract_model(prompt),
            prompt=prompt,
            response=payload,
            usage=_extract_usage_from_json(payload),
            started_at=started_at,
            ended_at=_utc_now(),
            storage=self.storage,
        )
        return response

    async def aclose(self) -> None:
        if hasattr(self.wrapped, "aclose"):
            await self.wrapped.aclose()


def instrument_httpx(client: Any, *, storage: Storage | str | None = None, provider: str | None = None) -> Any:
    if getattr(client, "_blackboxd_httpx_instrumented", False):
        return client

    if hasattr(client, "_transport"):
        client._transport = BlackboxdTransport(client._transport, storage=storage, provider=provider)
        client._blackboxd_httpx_instrumented = True
        return client

    if hasattr(client, "_transport_for_url"):
        original = client._transport_for_url

        def wrapped_transport_for_url(url: Any):
            transport = original(url)
            if hasattr(transport, "handle_async_request"):
                return AsyncBlackboxdTransport(transport, storage=storage, provider=provider)
            return BlackboxdTransport(transport, storage=storage, provider=provider)

        client._transport_for_url = wrapped_transport_for_url
        client._blackboxd_httpx_instrumented = True
        return client

    raise RuntimeError("Unsupported httpx client shape for instrumentation.")


def build_httpx_client(*, storage: Storage | str | None = None, provider: str | None = None, **kwargs):
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError("httpx is required. Install blackboxd[httpx].") from exc

    transport = kwargs.pop("transport", None) or httpx.HTTPTransport()
    return httpx.Client(
        transport=BlackboxdTransport(transport, storage=storage, provider=provider),
        **kwargs,
    )


def build_async_httpx_client(*, storage: Storage | str | None = None, provider: str | None = None, **kwargs):
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError("httpx is required. Install blackboxd[httpx].") from exc

    transport = kwargs.pop("transport", None) or httpx.AsyncHTTPTransport()
    return httpx.AsyncClient(
        transport=AsyncBlackboxdTransport(transport, storage=storage, provider=provider),
        **kwargs,
    )
