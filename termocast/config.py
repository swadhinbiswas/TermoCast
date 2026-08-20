"""Configuration — JSON file at ~/.config/termocast/config.json with sane defaults."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

from .constants import (
    CONFIG_FILE,
    CONFIG_DIR,
    DEFAULT_STOCKS,
    DEFAULT_CRYPTO,
    DEFAULT_NEWS_CATEGORY,
    DEFAULT_REFRESH_INTERVAL,
    CACHE_TTL,
)


@dataclass
class Config:
    city: Optional[str] = None  # None = auto-detect
    stocks: List[str] = field(default_factory=lambda: list(DEFAULT_STOCKS))
    crypto: List[str] = field(default_factory=lambda: list(DEFAULT_CRYPTO))
    news_category: str = DEFAULT_NEWS_CATEGORY
    news_sources: List[str] = field(default_factory=lambda: ["hackernews", "bbc"])
    refresh_interval: int = DEFAULT_REFRESH_INTERVAL
    theme: str = "termocast-dark"
    cache_ttl: dict = field(default_factory=lambda: dict(CACHE_TTL))
    show_sparkline: bool = True
    units: str = "metric"  # metric | imperial

    def save(self, path: Path = CONFIG_FILE):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> "Config":
        if not path.exists():
            cfg = cls()
            cfg.save(path)
            return cfg
        try:
            data = json.loads(path.read_text())
            # merge with defaults for missing keys
            defaults = asdict(cls())
            defaults.update({k: v for k, v in data.items() if v is not None})
            # ensure list copies
            return cls(**{k: v for k, v in defaults.items() if k in cls.__dataclass_fields__})
        except Exception:
            return cls()

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.save()


def load_config() -> Config:
    return Config.load()


def get_config_path() -> Path:
    return CONFIG_FILE
