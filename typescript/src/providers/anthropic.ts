import type { Storage } from "../storage/base.ts";
import { captureLlmCall } from "../capture.ts";
import type { TokenUsage } from "../types.ts";
import { utcNowIso } from "../utils.ts";

function extractUsage(response: unknown): TokenUsage | undefined {
  if (!response || typeof response !== "object") {
    return undefined;
  }

  const usage = (response as { usage?: Record<string, unknown> }).usage;
  if (!usage) {
    return undefined;
  }

  return {
    inputTokens: typeof usage.input_tokens === "number" ? usage.input_tokens : undefined,
    outputTokens: typeof usage.output_tokens === "number" ? usage.output_tokens : undefined,
  };
}

export class AnthropicWrapper {
  client: {
    messages: { create: (input: Record<string, unknown>) => Promise<unknown> };
  };
  provider: string;
  storage?: Storage | string;

  constructor(
    client: {
      messages: { create: (input: Record<string, unknown>) => Promise<unknown> };
    },
    options: { provider?: string; storage?: Storage | string } = {},
  ) {
    this.client = client;
    this.provider = options.provider ?? "anthropic";
    this.storage = options.storage;
  }

  messages = {
    create: async (input: Record<string, unknown>): Promise<unknown> => {
      const startedAt = utcNowIso();
      try {
        const response = await this.client.messages.create(input);
        await captureLlmCall({
          name: "anthropic.messages.create",
          provider: this.provider,
          model: typeof input.model === "string" ? input.model : undefined,
          prompt: input,
          response,
          startedAt,
          endedAt: utcNowIso(),
          usage: extractUsage(response),
          storage: this.storage,
        });
        return response;
      } catch (error) {
        await captureLlmCall({
          name: "anthropic.messages.create",
          provider: this.provider,
          model: typeof input.model === "string" ? input.model : undefined,
          prompt: input,
          startedAt,
          endedAt: utcNowIso(),
          error,
          storage: this.storage,
        });
        throw error;
      }
    },
  };
}
