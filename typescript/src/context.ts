import { AsyncLocalStorage } from "node:async_hooks";

import { getConfig } from "./config.ts";
import { toJsonable } from "./serialization.ts";
import { JSONLStorage } from "./storage/jsonl.ts";
import type { Storage } from "./storage/base.ts";
import type { ActiveSpan, EventKind, TraceEvent } from "./types.ts";
import { createId, utcNowIso } from "./utils.ts";

const spanStore = new AsyncLocalStorage<ActiveSpan[]>();

export function currentSpan(): ActiveSpan | undefined {
  const stack = spanStore.getStore();
  return stack?.[stack.length - 1];
}

export function withSpanContext<T>(span: ActiveSpan, fn: () => Promise<T>): Promise<T> {
  const stack = [...(spanStore.getStore() ?? []), span];
  return spanStore.run(stack, fn);
}

export function resolveStorage(storage?: Storage | string): Storage {
  if (!storage) {
    return getConfig().storage;
  }

  if (typeof storage === "string") {
    return new JSONLStorage(storage);
  }

  return storage;
}

export function newSpan(
  name: string,
  options: {
    tags?: string[];
    metadata?: Record<string, unknown>;
  } = {},
): ActiveSpan {
  const parent = currentSpan();
  return {
    traceId: parent?.traceId ?? createId(),
    spanId: createId(),
    parentSpanId: parent?.spanId,
    name,
    tags: [...(options.tags ?? [])],
    metadata: { ...(options.metadata ?? {}) },
  };
}

export function buildEvent(input: {
  kind: EventKind;
  name: string;
  span: ActiveSpan;
  provider?: string;
  model?: string;
  prompt?: unknown;
  response?: unknown;
  tags?: string[];
  metadata?: Record<string, unknown>;
}): TraceEvent {
  const config = getConfig();
  return {
    id: createId(),
    kind: input.kind,
    name: input.name,
    createdAt: utcNowIso(),
    traceId: input.span.traceId,
    spanId: input.span.spanId,
    parentSpanId: input.span.parentSpanId,
    provider: input.provider,
    model: input.model,
    prompt: toJsonable(input.prompt),
    response: toJsonable(input.response),
    metadata: toJsonable({
      ...config.defaultMetadata,
      ...input.span.metadata,
      ...(input.metadata ?? {}),
    }) as Record<string, unknown>,
    tags: [...config.defaultTags, ...input.span.tags, ...(input.tags ?? [])],
    environment: config.environment,
    appVersion: config.appVersion,
  };
}
