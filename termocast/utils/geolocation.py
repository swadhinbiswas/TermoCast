"""Geolocation helpers — IP-based, no API key needed, with fallbacks."""

from __future__ import annotations

import requests

from .cache import get_cache

_cache = get_cache("geolocation", ttl=3600)


def detect_location(timeout: int = 5) -> dict:
    """Detect city/country via multiple fallbacks. Returns dict with city, country, lat, lon."""
    cached = _cache.get("location")
    if cached:
        return cached

    # Try geocoder first (original dependency), then ip-api.com
    result = {"city": None, "country": None, "lat": None, "lon": None, "region": None}

    # Attempt 1: geocoder
    try:
        import geocoder
        g = geocoder.ip("me")
        if g and g.city:
            result.update({
                "city": g.city,
                "country": (g.country or "").lower() if g.country else None,
                "lat": g.lat if hasattr(g, "lat") else None,
                "lon": g.lng if hasattr(g, "lng") else None,
            })
            if result["city"]:
                _cache.set("location", result)
                return result
    except Exception:
        pass

    # Attempt 2: ip-api.com (no key)
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=timeout)
        if resp.status_code == 200:
            j = resp.json()
            if j.get("status") == "success":
                result.update({
                    "city": j.get("city"),
                    "country": (j.get("countryCode") or "").lower(),
                    "lat": j.get("lat"),
                    "lon": j.get("lon"),
                    "region": j.get("regionName"),
                })
                if result["city"]:
                    _cache.set("location", result)
                    return result
    except Exception:
        pass

    # Attempt 3: ipinfo fallback (no key limited)
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=timeout)
        if resp.status_code == 200:
            j = resp.json()
            city = j.get("city")
            if city:
                result["city"] = city
                result["country"] = (j.get("country") or "").lower()
                loc = j.get("loc", "")
                if "," in loc:
                    lat, lon = loc.split(",", 1)
                    result["lat"] = float(lat)
                    result["lon"] = float(lon)
                _cache.set("location", result)
                return result
    except Exception:
        pass

    return result


def resolve_city(city: str | None) -> str:
    """Resolve city string, falling back to detection or default."""
    if city and city.strip():
        return city.strip()
    loc = detect_location()
    if loc.get("city"):
        return loc["city"]
    return "London"  # final fallback
