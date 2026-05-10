from blackboxd import configure, instrument_openai


configure(
    storage=".blackboxd/instrument-existing-client.jsonl",
    environment="local",
    app_version="0.1.0",
)


class FakeUsage:
    input_tokens = 8
    output_tokens = 3


class FakeResponse:
    usage = FakeUsage()
    output_text = "Approved"


class FakeResponsesAPI:
    def create(self, **kwargs):
        return FakeResponse()


class FakeClient:
    def __init__(self):
        self.responses = FakeResponsesAPI()


client = instrument_openai(FakeClient())


if __name__ == "__main__":
    response = client.responses.create(model="gpt-4.1-mini", input="Review this receipt.")
    print(response.output_text)
