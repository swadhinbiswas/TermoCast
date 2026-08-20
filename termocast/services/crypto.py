"""Crypto service — CoinGecko markets (no key, free tier)."""

from __future__ import annotations

from typing import List

from .base import BaseService, ServiceResult
from ..constants import COINGECKO_MARKETS, CACHE_TTL
from ..utils.cache import get_cache
from ..utils.formatters import sparkline

_cache = get_cache("crypto", ttl=CACHE_TTL["crypto"])


class CryptoService(BaseService):
    name = "crypto"
    ttl = CACHE_TTL["crypto"]

    def fetch(self, ids: List[str] | None = None, vs_currency: str = "usd", force: bool = False) -> ServiceResult:
        ids = ids or ["bitcoin", "ethereum", "solana", "binancecoin"]
        ids = [i.lower().strip() for i in ids]
        key = f"crypto:{','.join(sorted(ids))}:{vs_currency}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)

        params = {
            "vs_currency": vs_currency,
            "ids": ",".join(ids),
            "order": "market_cap_desc",
            "per_page": len(ids),
            "page": 1,
            "sparkline": "true",
            "price_change_percentage": "24h,7d",
        }
        res = self._get(COINGECKO_MARKETS, params=params, timeout=10)
        if not res.ok:
            # CoinGecko rate limited? Try fallback with less ids
            if "429" in (res.error or ""):
                return ServiceResult(ok=False, error="CoinGecko rate-limited (429). Try again in 30s.")
            return res
        try:
            out = []
            for coin in res.data:
                spark = coin.get("sparkline_in_7d", {}).get("price", []) or []
                # thin to 30 points
                if len(spark) > 30:
                    step = len(spark) // 30
                    spark = spark[::step][:30]
                out.append({
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name"),
                    "price": coin.get("current_price"),
                    "market_cap": coin.get("market_cap"),
                    "volume": coin.get("total_volume"),
                    "change_24h": coin.get("price_change_percentage_24h"),
                    "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                    "spark": sparkline(spark),
                    "spark_raw": spark,
                    "image": coin.get("image"),
                    "rank": coin.get("market_cap_rank"),
                })
            self.cache.set(key, out)
            return ServiceResult(ok=True, data=out)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))

    def top(self, vs_currency: str = "usd", per_page: int = 10, force: bool = False) -> ServiceResult:
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "true",
            "price_change_percentage": "24h",
        }
        key = f"crypto:top:{vs_currency}:{per_page}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)
        res = self._get(COINGECKO_MARKETS, params=params, timeout=10)
        if not res.ok:
            return res
        try:
            out = []
            for coin in res.data:
                spark = coin.get("sparkline_in_7d", {}).get("price", []) or []
                if len(spark) > 30:
                    step = len(spark)//30
                    spark = spark[::step][:30]
                out.append({
                    "id": coin.get("id"),
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name"),
                    "price": coin.get("current_price"),
                    "change_24h": coin.get("price_change_percentage_24h"),
                    "spark": sparkline(spark),
                })
            self.cache.set(key, out)
            return ServiceResult(ok=True, data=out)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))


_service = CryptoService()


def get_crypto(ids: List[str] | None = None, vs_currency: str = "usd", force: bool = False) -> ServiceResult:
    return _service.fetch(ids=ids, vs_currency=vs_currency, force=force)
