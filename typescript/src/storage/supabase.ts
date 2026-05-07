import type { TraceEvent } from "../types.ts";
import type { Storage } from "./base.ts";

const CREATE_TABLE_SQL = `
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
`;

const INSERT_SQL = `
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
  $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
  $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
)
`;

export class SupabaseStorage implements Storage {
  dsn: string;
  pool?: {
    connect: () => Promise<{ query: (sql: string) => Promise<unknown>; release: () => void }>;
    query: (sql: string, values?: unknown[]) => Promise<unknown>;
  };
  ready: Promise<void>;

  constructor(dsn: string, options: { ensureTable?: boolean } = {}) {
    this.dsn = dsn;
    this.ready = options.ensureTable === false ? Promise.resolve() : this.ensureTable();
  }

  async getPool() {
    if (this.pool) {
      return this.pool;
    }

    let module: { default?: { Pool: new (options: { connectionString: string }) => unknown }; Pool?: new (options: { connectionString: string }) => unknown };
    try {
      module = await import("pg");
    } catch (error) {
      throw new Error("pg is required for SupabaseStorage. Run npm install in typescript/.");
    }

    const Pool = module.default?.Pool ?? module.Pool;
    if (!Pool) {
      throw new Error("pg.Pool is not available.");
    }

    this.pool = new Pool({ connectionString: this.dsn }) as SupabaseStorage["pool"];
    return this.pool;
  }

  async ensureTable(): Promise<void> {
    const pool = await this.getPool();
    const client = await pool.connect();
    try {
      await client.query(CREATE_TABLE_SQL);
    } finally {
      client.release();
    }
  }

  async writeEvent(event: TraceEvent): Promise<void> {
    await this.ready;
    const pool = await this.getPool();
    await pool.query(INSERT_SQL, [
      event.id,
      event.kind,
      event.name,
      event.createdAt,
      event.endedAt ?? null,
      event.traceId,
      event.spanId,
      event.parentSpanId ?? null,
      event.provider ?? null,
      event.model ?? null,
      event.prompt ?? null,
      event.response ?? null,
      event.metadata,
      event.tags,
      event.latencyMs ?? null,
      event.inputTokens ?? null,
      event.outputTokens ?? null,
      event.error ?? null,
      event.environment ?? null,
      event.appVersion ?? null,
    ]);
  }
}
