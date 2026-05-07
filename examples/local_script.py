from blackboxd import OpenAI, configure, trace_llm, trace_span


configure(
    storage=".blackboxd/local-script.jsonl",
    environment="local",
    app_version="0.1.0",
    default_tags=["batch-review"],
)

client = OpenAI()


@trace_llm(tags=["receipt-review"])
def review_receipt(receipt_text: str) -> str:
    with trace_span("classify", metadata={"document_type": "receipt"}):
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": receipt_text}],
                }
            ],
        )
    return response.output_text


if __name__ == "__main__":
    print(review_receipt("Store: Coffee Lab, Amount: 12.40 USD, Please summarize."))
