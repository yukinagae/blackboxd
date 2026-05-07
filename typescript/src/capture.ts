import { buildEvent, currentSpan, newSpan, resolveStorage } from "./context.ts";
import { toJsonable } from "./serialization.ts";
import type { Storage } from "./storage/base.ts";
import type { TokenUsage } from "./types.ts";
import { createId, durationMs, utcNowIso } from "./utils.ts";

export async function captureLlmCall(input: {
  name: string;
  provider: string;
  model?: string;
  prompt: unknown;
  response?: unknown;
  startedAt?: string;
  endedAt?: string;
  error?: unknown;
  usage?: TokenUsage;
  tags?: string[];
  metadata?: Record<string, unknown>;
  storage?: Storage | string;
}): Promise<void> {
  const active = currentSpan();
  const span = active ?? newSpan(input.name);
  const event = buildEvent({
    kind: "llm",
    name: input.name,
    span,
    provider: input.provider,
    model: input.model,
    prompt: input.prompt,
    response: input.response,
    tags: input.tags,
    metadata: input.metadata,
  });

  event.spanId = createId();
  event.parentSpanId = active?.spanId ?? span.parentSpanId;
  event.createdAt = input.startedAt ?? utcNowIso();
  event.endedAt = input.endedAt ?? utcNowIso();
  event.latencyMs = durationMs(event.createdAt, event.endedAt);
  event.response = toJsonable(input.response);
  event.error = input.error
    ? input.error instanceof Error
      ? `${input.error.name}: ${input.error.message}`
      : String(input.error)
    : undefined;
  event.inputTokens = input.usage?.inputTokens;
  event.outputTokens = input.usage?.outputTokens;

  await resolveStorage(input.storage).writeEvent(event);
}
