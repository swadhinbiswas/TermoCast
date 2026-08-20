"""Base service with retry, timeout, and structured errors."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional
import requests

from ..utils.cache import TTLCache, get_cache


@dataclass
class ServiceResult:
    ok: bool
    data: Any = None
    error: Optional[str] = None
    cached: bool = False
    latency_ms: int = 0

    def to_dict(self):
        return {"ok": self.ok, "data": self.data, "error": self.error, "cached": self.cached, "latency_ms": self.latency_ms}


class BaseService:
    name: str = "base"
    ttl: int = 300

    def __init__(self, ttl: Optional[int] = None):
        self.ttl = ttl if ttl is not None else self.ttl
        self.cache: TTLCache = get_cache(self.name, ttl=self.ttl)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "TermoCast/1.0 (+https://github.com/swadhinbiswas/TermoCast)"})

    def _get(self, url: str, params: dict | None = None, timeout: int = 8, retries: int = 1) -> ServiceResult:
        start = time.time()
        last_err = None
        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=timeout)
                latency = int((time.time() - start) * 1000)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        data = resp.text
                    return ServiceResult(ok=True, data=data, latency_ms=latency)
                else:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_err = str(e)
                time.sleep(0.3 * (attempt + 1))
        latency = int((time.time() - start) * 1000)
        return ServiceResult(ok=False, error=last_err or "Unknown error", latency_ms=latency)

    def cached_get(self, key: str, url: str, params: dict | None = None, force: bool = False) -> ServiceResult:
        if not force:
            cached = self.cache.get(key)
            if cached is not None:
                # cached is already ServiceResult dict or data
                if isinstance(cached, dict) and "ok" in cached:
                    # reconstruct
                    cached["cached"] = True
                    return ServiceResult(**cached)
                return ServiceResult(ok=True, data=cached, cached=True)
        res = self._get(url, params=params)
        if res.ok:
            self.cache.set(key, res.to_dict())
        return res
