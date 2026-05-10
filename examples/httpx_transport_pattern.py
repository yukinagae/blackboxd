from blackboxd import BlackboxdTransport, JSONLStorage, configure


configure(
    storage=JSONLStorage(".blackboxd/httpx-transport.jsonl"),
    environment="local",
    app_version="0.1.0",
)


class FakeURL:
    host = "api.openai.com"


class FakeRequest:
    url = FakeURL()
    content = b'{"model":"gpt-4.1-mini","input":"Review this receipt."}'


class FakeResponse:
    text = '{"output_text":"Approved","usage":{"input_tokens":8,"output_tokens":3}}'

    def json(self):
        import json

        return json.loads(self.text)


class FakeHTTPTransport:
    def handle_request(self, request):
        return FakeResponse()


if __name__ == "__main__":
    transport = BlackboxdTransport(FakeHTTPTransport())
    response = transport.handle_request(FakeRequest())
    print(response.json()["output_text"])
