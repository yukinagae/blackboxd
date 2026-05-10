import json
import unittest
from pathlib import Path

from blackboxd import configure, record_io, trace, trace_llm, trace_span, wrap_io_call


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

    def test_generic_trace_and_record_io_write_input_output(self):
        tmp_path = Path("/tmp")
        log_path = tmp_path / "blackboxd-generic-io.jsonl"
        if log_path.exists():
            log_path.unlink()

        configure(storage=str(log_path), environment="test", app_version="2.0.0")

        @trace(tags=["generic"])
        def run():
            record_io(
                name="transform",
                input_data={"value": "abc"},
                output_data={"value": "ABC"},
                metadata={"stage": "transform"},
            )
            return "ok"

        self.assertEqual(run(), "ok")

        events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").strip().splitlines()]
        io_events = [event for event in events if event["kind"] == "io"]
        self.assertEqual(len(io_events), 1)
        self.assertEqual(io_events[0]["input"], {"value": "abc"})
        self.assertEqual(io_events[0]["output"], {"value": "ABC"})
        self.assertEqual(io_events[0]["metadata"]["stage"], "transform")

    def test_wrap_io_call_records_function_io(self):
        tmp_path = Path("/tmp")
        log_path = tmp_path / "blackboxd-wrap-io.jsonl"
        if log_path.exists():
            log_path.unlink()

        configure(storage=str(log_path), environment="test", app_version="2.0.0")

        wrapped = wrap_io_call(
            lambda value: value.upper(),
            name="uppercase",
            input_mapper=lambda value: {"value": value},
        )
        self.assertEqual(wrapped("hello"), "HELLO")

        events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").strip().splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "io")
        self.assertEqual(events[0]["input"], {"value": "hello"})
        self.assertEqual(events[0]["output"], "HELLO")
