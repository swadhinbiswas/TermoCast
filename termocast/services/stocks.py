"""Stocks service — Yahoo Finance chart API (no key), with sparkline support."""

from __future__ import annotations

import time
from typing import List, Dict, Any

from .base import BaseService, ServiceResult
from ..constants import YAHOO_QUOTE_URL, YAHOO_SPARK_URL, CACHE_TTL
from ..utils.cache import get_cache
from ..utils.formatters import sparkline

_cache = get_cache("stocks", ttl=CACHE_TTL["stocks"])


class StockService(BaseService):
    name = "stocks"
    ttl = CACHE_TTL["stocks"]

    def fetch_one(self, symbol: str, force: bool = False) -> ServiceResult:
        symbol = symbol.upper().strip()
        key = f"stock:{symbol}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)

        url = YAHOO_QUOTE_URL.format(symbol=symbol)
        res = self._get(url, timeout=8)
        if not res.ok:
            return res
        try:
            j = res.data
            chart = j.get("chart", {})
            result = (chart.get("result") or [None])[0]
            if not result:
                return ServiceResult(ok=False, error=f"No data for {symbol}: {chart.get('error')}")
            meta = result.get("meta", {})
            indicators = result.get("indicators", {}).get("quote", [{}])[0]
            closes = indicators.get("close", []) or []
            # filter Nones
            closes = [c for c in closes if c is not None]
            timestamps = result.get("timestamp", []) or []

            price = meta.get("regularMarketPrice")
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")
            change = (price - prev) if price is not None and prev else 0
            change_pct = (change / prev * 100) if prev else 0

            parsed = {
                "symbol": symbol,
                "shortName": meta.get("shortName") or meta.get("longName") or symbol,
                "currency": meta.get("currency", "USD"),
                "price": price,
                "previousClose": prev,
                "change": change,
                "changePercent": change_pct,
                "dayHigh": meta.get("regularMarketDayHigh"),
                "dayLow": meta.get("regularMarketDayLow"),
                "volume": meta.get("regularMarketVolume"),
                "marketState": meta.get("marketState"),
                "spark": sparkline(closes[-30:] if len(closes) > 30 else closes),
                "closes": closes[-30:],
                "timestamps": timestamps[-30:],
                "meta": meta,
            }
            self.cache.set(key, parsed)
            return ServiceResult(ok=True, data=parsed)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))

    def fetch_many(self, symbols: List[str], force: bool = False) -> ServiceResult:
        """Fetch multiple symbols (sequential, cached). Uses spark endpoint batched for efficiency if >3."""
        symbols = [s.upper().strip() for s in symbols if s.strip()]
        if not symbols:
            return ServiceResult(ok=False, error="No symbols")
        key = f"stocks:many:{','.join(sorted(symbols))}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)

        # Try batched spark endpoint first for speed (when >2)
        if len(symbols) >= 3:
            try:
                url = YAHOO_SPARK_URL.format(symbols=",".join(symbols))
                res = self._get(url, timeout=8)
                if res.ok:
                    spark_data = res.data.get("spark", {}).get("result", [])
                    # map by symbol
                    mapped = {r.get("symbol"): r for r in spark_data}
                    results = []
                    errors = []
                    for sym in symbols:
                        # still fetch single for accurate meta if spark missing price
                        if sym in mapped and mapped[sym].get("response"):
                            # spark response contains close + timestamp but not meta; fallback to fetch_one for meta
                            r = self.fetch_one(sym, force=force)
                            if r.ok:
                                results.append(r.data)
                            else:
                                errors.append(f"{sym}: {r.error}")
                        else:
                            r = self.fetch_one(sym, force=force)
                            if r.ok:
                                results.append(r.data)
                            else:
                                errors.append(f"{sym}: {r.error}")
                    if results:
                        self.cache.set(key, results)
                        return ServiceResult(ok=True, data=results, error="; ".join(errors) if errors else None)
            except Exception:
                pass

        # Fallback sequential
        results = []
        errors = []
        for sym in symbols:
            r = self.fetch_one(sym, force=force)
            if r.ok:
                results.append(r.data)
            else:
                errors.append(f"{sym}: {r.error}")
        if not results:
            return ServiceResult(ok=False, error="; ".join(errors))
        self.cache.set(key, results)
        return ServiceResult(ok=True, data=results, error="; ".join(errors) if errors else None)

    def search_symbol(self, query: str) -> ServiceResult:
        """Use Yahoo search (no key) to autocomplete symbols."""
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=6&newsCount=0"
            res = self._get(url, timeout=6)
            if not res.ok:
                return res
            quotes = res.data.get("quotes", [])
            out = [{"symbol": q.get("symbol"), "name": q.get("shortname") or q.get("longname"), "type": q.get("quoteType")} for q in quotes]
            return ServiceResult(ok=True, data=out)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))


_service = StockService()


def get_stocks(symbols: List[str], force: bool = False) -> ServiceResult:
    return _service.fetch_many(symbols, force=force)
