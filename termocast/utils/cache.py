"""Tiny TTL cache — thread-safe, no deps, JSON-serializable fallback."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Optional
from functools import wraps

try:
    from ..constants import CACHE_DIR
except ImportError:
    CACHE_DIR = Path.home() / ".cache" / "termocast"


class TTLCache:
    """In-memory TTL cache with optional disk persistence."""

    def __init__(self, ttl: int = 300, maxsize: int = 128, persist_path: Optional[Path] = None):
        self.ttl = ttl
        self.maxsize = maxsize
        self.persist_path = persist_path
        self._store: dict[str, tuple[float, Any]] = {}
        if persist_path and persist_path.exists():
            try:
                data = json.loads(persist_path.read_text())
                now = time.time()
                for k, (exp, v) in data.items():
                    if exp > now:
                        self._store[k] = (exp, v)
            except Exception:
                pass

    def _persist(self):
        if not self.persist_path:
            return
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            serializable = {}
            for k, (exp, v) in self._store.items():
                try:
                    json.dumps(v)
                    serializable[k] = (exp, v)
                except Exception:
                    continue
            self.persist_path.write_text(json.dumps(serializable))
        except Exception:
            pass

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        exp, val = item
        if time.time() > exp:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if len(self._store) >= self.maxsize:
            # evict oldest
            oldest = min(self._store, key=lambda k: self._store[k][0])
            self._store.pop(oldest, None)
        exp = time.time() + (ttl if ttl is not None else self.ttl)
        self._store[key] = (exp, value)
        self._persist()

    def clear(self):
        self._store.clear()
        if self.persist_path and self.persist_path.exists():
            try:
                self.persist_path.unlink()
            except Exception:
                pass

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None


# Global caches per domain
_global_caches: dict[str, TTLCache] = {}


def get_cache(name: str, ttl: int = 300) -> TTLCache:
    if name not in _global_caches:
        path = CACHE_DIR / f"{name}.json"
        _global_caches[name] = TTLCache(ttl=ttl, persist_path=path)
    return _global_caches[name]


def cached(cache_name: str, ttl: int = 300, key_fn: Optional[Callable] = None):
    """Decorator for sync functions using TTLCache."""
    def decorator(fn: Callable):
        cache = get_cache(cache_name, ttl)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = f"{fn.__name__}:{args}:{sorted(kwargs.items())}"
            val = cache.get(key)
            if val is not None:
                return val
            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result
        wrapper.cache = cache  # type: ignore
        return wrapper
    return decorator
