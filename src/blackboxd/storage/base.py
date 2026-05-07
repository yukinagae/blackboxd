from __future__ import annotations

from abc import ABC, abstractmethod

from blackboxd.models import TraceEvent


class Storage(ABC):
    @abstractmethod
    def write_event(self, event: TraceEvent) -> None:
        raise NotImplementedError
