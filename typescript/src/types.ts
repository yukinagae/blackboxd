export type EventKind = "span" | "llm";

export interface TokenUsage {
  inputTokens?: number;
  outputTokens?: number;
}

export interface TraceEvent {
  id: string;
  kind: EventKind;
  name: string;
  createdAt: string;
  endedAt?: string;
  latencyMs?: number;
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  provider?: string;
  model?: string;
  prompt?: unknown;
  response?: unknown;
  metadata: Record<string, unknown>;
  tags: string[];
  inputTokens?: number;
  outputTokens?: number;
  error?: string;
  environment?: string;
  appVersion?: string;
}

export interface ActiveSpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  name: string;
  tags: string[];
  metadata: Record<string, unknown>;
}
