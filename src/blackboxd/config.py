from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from blackboxd.storage.base import Storage
from blackboxd.storage.jsonl import JSONLStorage


@dataclass(slots=True)
class BlackboxdConfig:
    storage: Storage = field(default_factory=JSONLStorage)
    environment: str = "development"
    app_version: str = "0.0.0"
    default_tags: list[str] = field(default_factory=list)
    default_metadata: dict[str, Any] = field(default_factory=dict)


_CONFIG = BlackboxdConfig()


def configure(
    *,
    storage: Storage | str | None = None,
    environment: str | None = None,
    app_version: str | None = None,
    default_tags: list[str] | None = None,
    default_metadata: dict[str, Any] | None = None,
) -> BlackboxdConfig:
    global _CONFIG
    if isinstance(storage, str):
        storage = JSONLStorage(storage)
    if storage is not None:
        _CONFIG.storage = storage
    if environment is not None:
        _CONFIG.environment = environment
    if app_version is not None:
        _CONFIG.app_version = app_version
    if default_tags is not None:
        _CONFIG.default_tags = list(default_tags)
    if default_metadata is not None:
        _CONFIG.default_metadata = dict(default_metadata)
    return _CONFIG


def get_config() -> BlackboxdConfig:
    return _CONFIG
