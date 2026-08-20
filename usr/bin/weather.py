"""
Legacy shim — preserved for backward compatibility.
Delegates to termocast.services.weather.WeatherService.
Kept side-effect-free on import (no auto-execution).
Use `weather` or `termocast weather` console_scripts instead.
"""

from __future__ import annotations

import re
import requests
import geocoder
from rich.console import Console
from rich.panel import Panel
import typer

app = typer.Typer(help="Legacy weather CLI shim — use `termocast weather` instead")

def style_text(text: str):
    console = Console()
    panel = Panel(text, title='WeatherCli ⛅️ by @swadhinbiswas', style='bold green', border_style='bold green', title_align="center")
    console.print(panel, justify="center")

def findcity():
    try:
        g = geocoder.ip('me')
        return g.city or "London"
    except Exception:
        return "London"

def findcountry():
    try:
        g = geocoder.ip('me')
        return (g.country or "").lower()
    except Exception:
        return ""

def remove_text(text: str, pattern: str):
    return re.sub(pattern, '', text)

def weather(city: str | None = None):
    """
    Fetches and displays the weather forecast.
    Now delegates to termocast.services.weather for robustness,
    but preserves original text output for compatibility.
    """
    # Prefer new service if available
    try:
        from termocast.services.weather import WeatherService
        svc = WeatherService()
        res = svc.fetch(city or findcity())
        if res.ok and "raw_text" not in res.data:
            # render via new rich path still print legacy style
            data = res.data
            cur = data.get("current", {})
            city_disp = data.get("city") or city or findcity()
            style_text(f"Weather forecast for {city_disp}")
            # also print legacy text for familiarity
            try:
                url = f"https://wttr.in/{city_disp}"
                resp = requests.get(url, verify=False, timeout=8)
                if resp.status_code == 200:
                    text = resp.text[:-127] if len(resp.text) > 200 else resp.text
                    print(text)
                    return
            except Exception:
                pass
            # fallback to JSON summary
            print(f"{city_disp} — {cur.get('weatherDesc','')} {cur.get('temp_C','—')}°C")
            return
        elif res.ok and "raw_text" in res.data:
            city_disp = res.data.get("city") or city or findcity()
            style_text(f"Weather forecast for {city_disp}")
            print(res.data["raw_text"])
            return
    except Exception:
        pass

    # Ultimate legacy fallback (original behaviour)
    city = city or findcity()
    url = f'https://wttr.in/{city}'
    try:
        response = requests.get(url, verify=False, timeout=8)
    except Exception:
        print('Could not get weather forecast for', city)
        return
    if response.status_code == 200:
        text = response.text[:-127] if len(response.text) > 127 else response.text
        style_text(f"Weather forecast for {city}")
        print(text)
    else:
        print('Could not get weather forecast for', city)

# Only run when executed as script, not on import
if __name__ == "__main__":
    weather()
