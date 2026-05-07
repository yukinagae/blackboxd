import json
import unittest
from pathlib import Path

from blackboxd import configure, trace_llm, trace_span


class TraceJSONLTest(unittest.TestCase):
    def test_trace_llm_and_span_write_jsonl(self):
        tmp_path = Path("/tmp")
        log_path = tmp_path / "blackboxd-test-events.jsonl"
        if log_path.exists():
            log_path.unlink()

        configure(storage=str(log_path), environment="test", app_version="1.2.3")

        @trace_llm(tags=["unit"])
        def run():
            with trace_span("nested", metadata={"step": "nested"}):
                return "ok"

        self.assertEqual(run(), "ok")

        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)

        events = [json.loads(line) for line in lines]
        self.assertEqual({event["kind"] for event in events}, {"span"})
        self.assertTrue(all(event["trace_id"] for event in events))
        self.assertTrue(any(event["name"] == "nested" for event in events))
        self.assertTrue(all(event["environment"] == "test" for event in events))
