from __future__ import annotations

import json
from pathlib import Path

from blackboxd.models import TraceEvent
from blackboxd.storage.base import Storage


class JSONLStorage(Storage):
    def __init__(self, path: str = ".blackboxd/logs.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write_event(self, event: TraceEvent) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False))
            handle.write("\n")
