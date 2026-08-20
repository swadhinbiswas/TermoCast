"""News service — HackerNews (Algolia) + BBC RSS, no API keys, with local RSS parser."""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from typing import List, Dict

from .base import BaseService, ServiceResult
from ..constants import HN_ALGOLIA_URL, RSS_FEEDS, CACHE_TTL
from ..utils.cache import get_cache

_cache = get_cache("news", ttl=CACHE_TTL["news"])


class NewsService(BaseService):
    name = "news"
    ttl = CACHE_TTL["news"]

    def fetch_hn(self, limit: int = 20, force: bool = False) -> ServiceResult:
        key = f"hn:{limit}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)
        res = self._get(HN_ALGOLIA_URL, timeout=8)
        if not res.ok:
            return res
        try:
            hits = res.data.get("hits", [])[:limit]
            articles = []
            for h in hits:
                articles.append({
                    "title": h.get("title") or h.get("story_title") or "Untitled",
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "points": h.get("points", 0),
                    "author": h.get("author", ""),
                    "num_comments": h.get("num_comments", 0),
                    "created_at": h.get("created_at", ""),
                    "source": "HackerNews",
                    "category": "technology",
                })
            self.cache.set(key, articles)
            return ServiceResult(ok=True, data=articles)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))

    def fetch_rss(self, category: str = "technology", force: bool = False) -> ServiceResult:
        category = category.lower()
        url = RSS_FEEDS.get(category, RSS_FEEDS["technology"])
        key = f"rss:{category}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)
        try:
            resp = self.session.get(url, timeout=8)
            if resp.status_code != 200:
                return ServiceResult(ok=False, error=f"RSS HTTP {resp.status_code}")
            articles = self._parse_rss(resp.text, category)
            self.cache.set(key, articles)
            return ServiceResult(ok=True, data=articles)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))

    def _parse_rss(self, xml_text: str, category: str) -> List[Dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            # try stripping junk
            xml_text = re.sub(r"^[^\n]*<\?xml", "<?xml", xml_text)
            root = ET.fromstring(xml_text)
        items = []
        # RSS 2.0: channel/item
        for item in root.findall(".//item")[:20]:
            title = item.findtext("title", default="Untitled")
            link = item.findtext("link", default="")
            desc = item.findtext("description", default="")
            pub = item.findtext("pubDate", default="")
            # clean html tags from desc
            desc = re.sub(r"<[^>]+>", "", desc)[:220]
            items.append({
                "title": title.strip(),
                "url": link.strip(),
                "description": desc.strip(),
                "published": pub,
                "source": f"BBC {category.title()}",
                "category": category,
            })
        return items

    def fetch(self, category: str = "technology", source: str = "all", limit: int = 20, force: bool = False) -> ServiceResult:
        """Unified fetch. source: hn | bbc | all"""
        key = f"news:{category}:{source}:{limit}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)

        all_articles: List[Dict] = []
        errors: List[str] = []

        if source in ("all", "hn", "hackernews"):
            r = self.fetch_hn(limit=limit, force=force)
            if r.ok:
                all_articles.extend(r.data)
            else:
                errors.append(f"HN: {r.error}")

        if source in ("all", "bbc", "rss"):
            r = self.fetch_rss(category=category, force=force)
            if r.ok:
                # interleave RSS
                all_articles.extend(r.data[:limit//2] if source == "all" else r.data)
            else:
                errors.append(f"RSS: {r.error}")

        if not all_articles:
            return ServiceResult(ok=False, error="; ".join(errors) or "No news fetched")

        # Dedupe by title
        seen = set()
        deduped = []
        for a in all_articles:
            t = a.get("title", "")
            if t not in seen:
                seen.add(t)
                deduped.append(a)
        deduped = deduped[:limit]
        self.cache.set(key, deduped)
        return ServiceResult(ok=True, data=deduped)

    def search(self, query: str, limit: int = 15) -> ServiceResult:
        """Search HN Algolia by query."""
        url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story"
        res = self._get(url, timeout=8)
        if not res.ok:
            return res
        try:
            hits = res.data.get("hits", [])[:limit]
            arts = [{
                "title": h.get("title", ""),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "points": h.get("points", 0),
                "author": h.get("author", ""),
                "source": "HackerNews Search",
            } for h in hits]
            return ServiceResult(ok=True, data=arts)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))


_service = NewsService()


def get_news(category: str = "technology", source: str = "all", limit: int = 20, force: bool = False) -> ServiceResult:
    return _service.fetch(category=category, source=source, limit=limit, force=force)
