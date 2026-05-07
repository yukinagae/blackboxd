from fastapi import FastAPI

from blackboxd import JSONLStorage, OpenAI, configure, trace_span


configure(
    storage=JSONLStorage(".blackboxd/fastapi.jsonl"),
    environment="development",
    app_version="0.1.0",
    default_tags=["api"],
)

client = OpenAI()
app = FastAPI()


@app.get("/review")
async def review_receipt(q: str):
    async with trace_span("review-request", metadata={"query": q}):
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=f"Review this receipt and return JSON: {q}",
        )
        return {"result": response.output_text}
