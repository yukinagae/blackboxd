import { configure, JSONLStorage, OpenAIWrapper, trace, traceSpan } from "../src/index.ts";

configure({
  storage: new JSONLStorage(".blackboxd/ts-local-script.jsonl"),
  environment: "local",
  appVersion: "0.1.0",
  defaultTags: ["typescript"],
});

const fakeClient = {
  responses: {
    async create(input: Record<string, unknown>) {
      return {
        id: "resp_123",
        model: input.model,
        output_text: "Approved",
        usage: { input_tokens: 12, output_tokens: 4 },
      };
    },
  },
};

const client = new OpenAIWrapper(fakeClient);

const reviewReceipt = trace("reviewReceipt", { tags: ["batch-review"] })(async (text: string) => {
  return traceSpan("classify", async () => {
    const response = (await client.responses.create({
      model: "gpt-4.1-mini",
      input: `Review this receipt: ${text}`,
    })) as { output_text: string };

    return response.output_text;
  });
});

console.log(await reviewReceipt("Store: Coffee Lab, Amount: 12.40 USD"));
