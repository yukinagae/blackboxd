from __future__ import annotations

from blackboxd.models import TraceEvent
from blackboxd.storage.base import Storage


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.llm_logs (
  id UUID PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  ended_at TIMESTAMPTZ NULL,
  trace_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  parent_span_id TEXT NULL,
  provider TEXT NULL,
  model TEXT NULL,
  prompt JSONB NULL,
  response JSONB NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags TEXT[] NOT NULL DEFAULT '{}',
  latency_ms INT NULL,
  input_tokens INT NULL,
  output_tokens INT NULL,
  error TEXT NULL,
  environment TEXT NULL,
  app_version TEXT NULL
);

CREATE INDEX IF NOT EXISTS llm_logs_created_at_idx ON public.llm_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS llm_logs_trace_id_idx ON public.llm_logs (trace_id);
CREATE INDEX IF NOT EXISTS llm_logs_provider_model_idx ON public.llm_logs (provider, model);
"""

INSERT_SQL = """
INSERT INTO public.llm_logs (
  id,
  kind,
  name,
  created_at,
  ended_at,
  trace_id,
  span_id,
  parent_span_id,
  provider,
  model,
  prompt,
  response,
  metadata,
  tags,
  latency_ms,
  input_tokens,
  output_tokens,
  error,
  environment,
  app_version
) VALUES (
  %(id)s,
  %(kind)s,
  %(name)s,
  %(created_at)s,
  %(ended_at)s,
  %(trace_id)s,
  %(span_id)s,
  %(parent_span_id)s,
  %(provider)s,
  %(model)s,
  %(prompt)s,
  %(response)s,
  %(metadata)s,
  %(tags)s,
  %(latency_ms)s,
  %(input_tokens)s,
  %(output_tokens)s,
  %(error)s,
  %(environment)s,
  %(app_version)s
)
"""


class SupabaseStorage(Storage):
    def __init__(self, dsn: str, *, ensure_table: bool = True) -> None:
        try:
            import psycopg
            from psycopg.types.json import Jsonb
        except ImportError as exc:
            raise RuntimeError(
                "psycopg is required for SupabaseStorage. Install blackboxd[supabase]."
            ) from exc

        self._psycopg = psycopg
        self._jsonb = Jsonb
        self.dsn = dsn
        if ensure_table:
            self.ensure_table()

    def ensure_table(self) -> None:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(CREATE_TABLE_SQL)
            conn.commit()

    def write_event(self, event: TraceEvent) -> None:
        payload = event.model_dump(mode="python")
        payload["metadata"] = self._jsonb(payload["metadata"])
        payload["prompt"] = self._jsonb(payload["prompt"]) if payload["prompt"] is not None else None
        payload["response"] = self._jsonb(payload["response"]) if payload["response"] is not None else None
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(INSERT_SQL, payload)
            conn.commit()
