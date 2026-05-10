import json
import unittest
from pathlib import Path

from blackboxd import (
    BlackboxdTransport,
    configure,
    instrument_httpx,
    instrument_openai,
    patch_openai,
)


class FakeUsage:
    input_tokens = 5
    output_tokens = 2


class FakeResponse:
    usage = FakeUsage()
    output_text = "ok"
    text = '{"output_text":"ok","usage":{"input_tokens":5,"output_tokens":2}}'

    def json(self):
        return json.loads(self.text)


class FakeResponsesAPI:
    def create(self, **kwargs):
        return FakeResponse()


class FakeChatCompletionsAPI:
    def create(self, **kwargs):
        return FakeResponse()


class FakeChatAPI:
    def __init__(self):
        self.completions = FakeChatCompletionsAPI()


class FakeClient:
    def __init__(self):
        self.responses = FakeResponsesAPI()
        self.chat = FakeChatAPI()


class FakeURL:
    host = "api.openai.com"


class FakeRequest:
    url = FakeURL()
    content = b'{"model":"gpt-4.1-mini","input":"hello"}'


class FakeHTTPTransport:
    def handle_request(self, request):
        return FakeResponse()


class FakeHTTPClient:
    def __init__(self):
        self._transport = FakeHTTPTransport()


class InstrumentationPatternsTest(unittest.TestCase):
    def setUp(self):
        self.log_path = Path("/tmp/blackboxd-patterns.jsonl")
        if self.log_path.exists():
            self.log_path.unlink()
        configure(storage=str(self.log_path), environment="test", app_version="1.2.3")

    def read_events(self):
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").strip().splitlines()
        ]

    def test_instrument_existing_client(self):
        client = instrument_openai(FakeClient())
        response = client.responses.create(model="gpt-4.1-mini", input="hello")
        self.assertEqual(response.output_text, "ok")
        events = self.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["name"], "openai.responses.create")
        self.assertEqual(events[0]["kind"], "llm")

    def test_monkey_patch(self):
        client = FakeClient()
        handles = patch_openai(client)
        try:
            response = client.chat.completions.create(model="gpt-4.1-mini", messages=[])
            self.assertEqual(response.output_text, "ok")
        finally:
            for handle in handles:
                handle.restore()
        events = self.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["name"], "openai.chat.completions.create")

    def test_http_transport_pattern(self):
        transport = BlackboxdTransport(FakeHTTPTransport())
        response = transport.handle_request(FakeRequest())
        self.assertEqual(response.output_text, "ok")
        events = self.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["provider"], "openai")
        self.assertEqual(events[0]["name"], "openai.http")

    def test_instrument_httpx_helper(self):
        client = instrument_httpx(FakeHTTPClient(), provider="openai")
        response = client._transport.handle_request(FakeRequest())
        self.assertEqual(response.output_text, "ok")
        events = self.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["provider"], "openai")
