"""Weather service — wttr.in JSON (no key) + geolocation + graceful fallback."""

from __future__ import annotations

import re
import requests
from typing import Any, Dict, List

from .base import BaseService, ServiceResult
from ..constants import WTTR_URL, CACHE_TTL
from ..utils.geolocation import detect_location, resolve_city
from ..utils.cache import get_cache

_cache = get_cache("weather", ttl=CACHE_TTL["weather"])


class WeatherService(BaseService):
    name = "weather"
    ttl = CACHE_TTL["weather"]

    def fetch(self, city: str | None = None, force: bool = False) -> ServiceResult:
        city_resolved = resolve_city(city)
        key = f"weather:{city_resolved.lower()}"
        if not force:
            cached = self.cache.get(key)
            if cached:
                return ServiceResult(ok=True, data=cached, cached=True)

        # Primary: wttr.in JSON
        url = WTTR_URL.format(city=city_resolved)
        try:
            resp = self.session.get(url, timeout=8)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    parsed = self._parse_wttr_json(data, city_resolved)
                    self.cache.set(key, parsed)
                    return ServiceResult(ok=True, data=parsed)
                except Exception as e:
                    # fall back to raw text slicing (legacy behaviour)
                    pass
        except Exception:
            pass

        # Fallback: wttr.in text with legacy slicing, then open-meteo if lat/lon available
        try:
            loc = detect_location()
            if loc.get("lat") and loc.get("lon"):
                return self._fetch_openmeteo(loc["lat"], loc["lon"], city_resolved, key)
        except Exception:
            pass

        # Final fallback: legacy text mode
        return self._fetch_legacy_text(city_resolved, key)

    def _parse_wttr_json(self, data: dict, city: str) -> dict:
        """Normalize wttr.in j1 JSON into our schema."""
        current = data.get("current_condition", [{}])[0]
        weather = data.get("weather", [])
        nearest = data.get("nearest_area", [{}])[0]

        # Extract location display
        area = nearest.get("areaName", [{}])[0].get("value", city) if nearest else city
        country = nearest.get("country", [{}])[0].get("value", "") if nearest else ""
        region = nearest.get("region", [{}])[0].get("value", "") if nearest else ""

        current_out = {
            "temp_C": current.get("temp_C"),
            "temp_F": current.get("temp_F"),
            "feelsLikeC": current.get("FeelsLikeC"),
            "humidity": current.get("humidity"),
            "windspeedKmph": current.get("windspeedKmph"),
            "winddir16Point": current.get("winddir16Point"),
            "weatherDesc": (current.get("weatherDesc", [{}])[0].get("value") if current.get("weatherDesc") else ""),
            "observation_time": current.get("observation_time"),
            "pressure": current.get("pressure"),
            "visibility": current.get("visibility"),
            "uvIndex": current.get("uvIndex"),
        }

        forecast: List[Dict[str, Any]] = []
        for day in weather[:3]:
            hourly = day.get("hourly", [])
            # pick midday as representative
            mid = hourly[4] if len(hourly) > 4 else (hourly[0] if hourly else {})
            forecast.append({
                "date": day.get("date"),
                "maxtempC": day.get("maxtempC"),
                "mintempC": day.get("mintempC"),
                "avg_hourly": mid,
                "hourly": hourly,
                "desc": (mid.get("weatherDesc", [{}])[0].get("value") if mid.get("weatherDesc") else ""),
            })

        return {
            "city": area,
            "country": country,
            "region": region,
            "requested_city": city,
            "current": current_out,
            "forecast": forecast,
            "source": "wttr.in",
            "raw": data,
        }

    def _fetch_openmeteo(self, lat: float, lon: float, city: str, cache_key: str) -> ServiceResult:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
                "forecast_days": 3,
            }
            resp = self.session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                j = resp.json()
                cw = j.get("current_weather", {})
                daily = j.get("daily", {})
                parsed = {
                    "city": city,
                    "country": "",
                    "region": "",
                    "requested_city": city,
                    "current": {
                        "temp_C": str(cw.get("temperature")),
                        "windspeedKmph": str(cw.get("windspeed")),
                        "weatherDesc": f"Wind {cw.get('winddirection')}°",
                        "observation_time": cw.get("time"),
                    },
                    "forecast": [
                        {
                            "date": daily.get("time", [])[i] if i < len(daily.get("time", [])) else "",
                            "maxtempC": str(daily.get("temperature_2m_max", [])[i]) if i < len(daily.get("temperature_2m_max", [])) else "",
                            "mintempC": str(daily.get("temperature_2m_min", [])[i]) if i < len(daily.get("temperature_2m_min", [])) else "",
                        }
                        for i in range(min(3, len(daily.get("time", []))))
                    ],
                    "source": "open-meteo",
                    "raw": j,
                }
                self.cache.set(cache_key, parsed)
                return ServiceResult(ok=True, data=parsed)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))
        return ServiceResult(ok=False, error="open-meteo failed")

    def _fetch_legacy_text(self, city: str, cache_key: str) -> ServiceResult:
        """Legacy text mode — mimics original behaviour but safely."""
        try:
            url = f"https://wttr.in/{city}"
            resp = self.session.get(url, timeout=8, verify=False)
            if resp.status_code == 200:
                # original sliced last 127 chars (footer). Do safer: strip ANSI footer if present
                text = resp.text
                # remove last 127 chars only if looks like footer
                if len(text) > 200:
                    text = text[:-127] if "Follow" in text[-200:] or "wttr.in" in text[-200:] else text
                parsed = {
                    "city": city,
                    "country": "",
                    "region": "",
                    "requested_city": city,
                    "current": {"weatherDesc": "See raw text"},
                    "forecast": [],
                    "raw_text": text,
                    "source": "wttr.in:text",
                }
                self.cache.set(cache_key, parsed)
                return ServiceResult(ok=True, data=parsed)
        except Exception as e:
            return ServiceResult(ok=False, error=str(e))
        return ServiceResult(ok=False, error="Weather fetch failed")

    # Convenience for CLI / textual sync context
    def get_text(self, city: str | None = None) -> str:
        res = self.fetch(city)
        if not res.ok:
            return f"[red]Could not get weather for {city}: {res.error}[/red]"
        data = res.data
        if "raw_text" in data:
            return data["raw_text"]
        # render quick rich-like summary if JSON
        cur = data.get("current", {})
        return f"{data.get('city')} — {cur.get('weatherDesc')} {cur.get('temp_C')}°C (humidity {cur.get('humidity')}%)"


# Singleton helper for simple imports
_service = WeatherService()


def get_weather(city: str | None = None, force: bool = False) -> ServiceResult:
    return _service.fetch(city, force=force)
