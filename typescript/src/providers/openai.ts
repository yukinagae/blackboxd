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
    inputTokens:
      typeof usage.input_tokens === "number"
        ? usage.input_tokens
        : typeof usage.prompt_tokens === "number"
          ? usage.prompt_tokens
          : undefined,
    outputTokens:
      typeof usage.output_tokens === "number"
        ? usage.output_tokens
        : typeof usage.completion_tokens === "number"
          ? usage.completion_tokens
          : undefined,
  };
}

export class OpenAIWrapper {
  client: {
    responses: { create: (input: Record<string, unknown>) => Promise<unknown> };
    chat?: {
      completions?: { create: (input: Record<string, unknown>) => Promise<unknown> };
    };
  };
  provider: string;
  storage?: Storage | string;

  constructor(
    client: {
      responses: { create: (input: Record<string, unknown>) => Promise<unknown> };
      chat?: {
        completions?: { create: (input: Record<string, unknown>) => Promise<unknown> };
      };
    },
    options: { provider?: string; storage?: Storage | string } = {},
  ) {
    this.client = client;
    this.provider = options.provider ?? "openai";
    this.storage = options.storage;
  }

  responses = {
    create: async (input: Record<string, unknown>): Promise<unknown> => {
      const startedAt = utcNowIso();
      try {
        const response = await this.client.responses.create(input);
        await captureLlmCall({
          name: "openai.responses.create",
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
          name: "openai.responses.create",
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

  chat = {
    completions: {
      create: async (input: Record<string, unknown>): Promise<unknown> => {
        if (!this.client.chat?.completions) {
          throw new Error("The wrapped client does not expose chat.completions.create.");
        }

        const startedAt = utcNowIso();
        try {
          const response = await this.client.chat.completions.create(input);
          await captureLlmCall({
            name: "openai.chat.completions.create",
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
            name: "openai.chat.completions.create",
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
    },
  };
}
