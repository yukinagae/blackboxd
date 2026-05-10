from blackboxd import configure, record_io, run_io, trace, trace_span


configure(
    storage=".blackboxd/generic-io.jsonl",
    environment="local",
    app_version="0.2.0",
    default_tags=["generic-io"],
)


@trace(tags=["pipeline"])
def review_document(text: str) -> dict:
    with trace_span("normalize"):
        normalized = text.strip().lower()

    result = run_io(
        "classify_document",
        lambda: {"label": "receipt", "confidence": 0.98},
        input_data={"text": normalized},
        metadata={"stage": "classification"},
    )

    record_io(
        name="persist_decision",
        input_data=result,
        output_data={"written": True},
        metadata={"sink": "database"},
    )
    return result


if __name__ == "__main__":
    print(review_document("Store: Coffee Lab, Amount: 12.40 USD"))
