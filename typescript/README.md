# blackboxd TypeScript SDK

`@blackboxd/sdk` is the Node and TypeScript version of `blackboxd`. It uses `AsyncLocalStorage` for trace propagation, JSONL for local-first logging, and Supabase Postgres for structured persistence.

## Install

```bash
cd typescript
npm install
```

## Quick Start

```ts
import { configure, OpenAIWrapper, traceLlm, traceSpan } from "@blackboxd/sdk";

configure({
  storage: ".blackboxd/logs.jsonl",
  environment: "development",
  appVersion: "0.1.0",
  defaultTags: ["receipt-review"],
});

const client = new OpenAIWrapper(openai);

const reviewReceipt = traceLlm("reviewReceipt", { tags: ["pipeline"] })(async (text: string) => {
  return traceSpan("classify", async () => {
    const response = await client.responses.create({
      model: "gpt-4.1-mini",
      input: `Review this receipt: ${text}`,
    });

    return response;
  });
});
```

## Core API

- `traceLlm(name, options)(fn)` wraps an async or sync function in a parent span.
- `trace(name, options)(fn)` is an alias if you want a shorter name.
- `traceSpan(name, fn, options)` creates a nested span around one specific step.
- `OpenAIWrapper` captures LLM events from `responses.create(...)` and `chat.completions.create(...)`.
- `AnthropicWrapper` captures LLM events from `messages.create(...)`.
- `SupabaseStorage` writes events to `public.llm_logs`.

## Supabase

```ts
import { configure, SupabaseStorage } from "@blackboxd/sdk";

configure({
  storage: new SupabaseStorage(process.env.SUPABASE_DB_DSN!),
});
```

Use a direct database connection string:

```bash
export SUPABASE_DB_DSN="postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require"
```

## Run The Example

```bash
node --experimental-strip-types examples/local-script.ts
```

## Run The Tests

```bash
npm test
```
