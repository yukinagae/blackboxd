from blackboxd import configure, patch_openai


configure(
    storage=".blackboxd/monkey-patch.jsonl",
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


client = FakeClient()
handles = patch_openai(client)


if __name__ == "__main__":
    try:
        response = client.responses.create(model="gpt-4.1-mini", input="Review this receipt.")
        print(response.output_text)
    finally:
        for handle in handles:
            handle.restore()
