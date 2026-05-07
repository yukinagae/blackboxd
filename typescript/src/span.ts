import { buildEvent, newSpan, resolveStorage, withSpanContext } from "./context.ts";
import { toJsonable } from "./serialization.ts";
import type { Storage } from "./storage/base.ts";
import { durationMs, utcNowIso } from "./utils.ts";

export async function traceSpan<T>(
  name: string,
  fn: () => Promise<T> | T,
  options: {
    tags?: string[];
    metadata?: Record<string, unknown>;
    storage?: Storage | string;
  } = {},
): Promise<T> {
  const span = newSpan(name, { tags: options.tags, metadata: options.metadata });
  const storage = resolveStorage(options.storage);
  const event = buildEvent({
    kind: "span",
    name,
    span,
    tags: options.tags,
    metadata: options.metadata,
  });
  const startedAt = event.createdAt;

  return withSpanContext(span, async () => {
    try {
      const result = await fn();
      const endedAt = utcNowIso();
      event.endedAt = endedAt;
      event.latencyMs = durationMs(startedAt, endedAt);
      await storage.writeEvent(event);
      return result;
    } catch (error) {
      const endedAt = utcNowIso();
      event.endedAt = endedAt;
      event.latencyMs = durationMs(startedAt, endedAt);
      event.error = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
      await storage.writeEvent(event);
      throw error;
    }
  });
}

export function trace(
  name?: string,
  options: {
    tags?: string[];
    metadata?: Record<string, unknown>;
    storage?: Storage | string;
  } = {},
) {
  return function wrap<TArgs extends unknown[], TResult>(
    fn: (...args: TArgs) => Promise<TResult> | TResult,
  ): (...args: TArgs) => Promise<TResult> {
    const spanName = name ?? fn.name ?? "anonymous";
    return async (...args: TArgs) =>
      traceSpan(
        spanName,
        () => fn(...args),
        {
          tags: options.tags,
          metadata: options.metadata,
          storage: options.storage,
        },
      );
  };
}
