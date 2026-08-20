"""Weather widget — rich rendering inside Textual."""

from __future__ import annotations

from textual.widgets import Static
from textual.app import ComposeResult
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group

from ..constants import WEATHER_EMOJI
from ..utils.formatters import format_date


class WeatherWidget(Static):
    """Displays current + 3-day forecast."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.weather_data: dict | None = None
        self.loading = True

    def update_weather(self, data: dict | None, error: str | None = None):
        self.loading = False
        if error:
            self.update(f"[red]Weather error: {error}[/red]")
            return
        if not data:
            self.update("[yellow]No weather data[/yellow]")
            return
        self.weather_data = data
        self.update(self._build_panel(data))

    def _build_panel(self, data: dict):
        city = data.get("city", data.get("requested_city", "Unknown"))
        country = data.get("country", "")
        region = data.get("region", "")
        loc = f"{city} {f'({region}, {country})' if country else ''}".strip()
        cur = data.get("current", {})
        desc = cur.get("weatherDesc", "") or cur.get("weatherDesc", "")
        emoji = "⛅"
        for k, v in WEATHER_EMOJI.items():
            if k.lower() in desc.lower():
                emoji = v
                break
        # fallback based on temp
        try:
            t = int(float(cur.get("temp_C", 0)))
            if "clear" in desc.lower() and t > 25:
                emoji = "☀️"
        except Exception:
            pass

        # Current table
        cur_table = Table(show_header=False, box=None, padding=(0, 1))
        cur_table.add_column("k", style="bold cyan")
        cur_table.add_column("v", style="white")
        cur_table.add_row("Condition", f"{emoji} {desc}")
        if cur.get("temp_C"):
            cur_table.add_row("Temp", f"[bold]{cur.get('temp_C')}°C[/] / {cur.get('temp_F')}°F  (feels {cur.get('feelsLikeC', '—')}°C)")
        if cur.get("humidity"):
            cur_table.add_row("Humidity", f"{cur.get('humidity')}%")
        if cur.get("windspeedKmph"):
            cur_table.add_row("Wind", f"{cur.get('windspeedKmph')} km/h {cur.get('winddir16Point','')}")
        if cur.get("visibility"):
            cur_table.add_row("Visibility", f"{cur.get('visibility')} km")
        if cur.get("pressure"):
            cur_table.add_row("Pressure", f"{cur.get('pressure')} hPa")
        if cur.get("uvIndex"):
            cur_table.add_row("UV Index", cur.get("uvIndex"))
        if cur.get("observation_time"):
            cur_table.add_row("Observed", cur.get("observation_time"))

        # Forecast table
        forecast = data.get("forecast", [])
        fc_table = Table(title="3-Day Forecast", show_header=True, header_style="bold magenta", box=None, padding=(0, 1))
        if forecast:
            fc_table.add_column("Date", style="cyan")
            fc_table.add_column("Max", justify="right", style="red")
            fc_table.add_column("Min", justify="right", style="blue")
            fc_table.add_column("Desc", style="white")
            for d in forecast:
                desc_fc = d.get("desc", "")[:28]
                emo = "⛅"
                for k, v in WEATHER_EMOJI.items():
                    if k.lower() in desc_fc.lower():
                        emo = v; break
                fc_table.add_row(
                    format_date(d.get("date")),
                    f"{d.get('maxtempC','—')}°C",
                    f"{d.get('mintempC','—')}°C",
                    f"{emo} {desc_fc}",
                )
        else:
            fc_table.add_row("—", "—", "—", "No forecast")

        # Raw text fallback
        if "raw_text" in data and not cur.get("temp_C"):
            return Panel(data["raw_text"], title=f"Weather — {loc}", border_style="green")

        group = Group(cur_table, Text(""), fc_table)
        return Panel(group, title=f"[bold green]{loc}[/]  [dim]{data.get('source','')}[/]", border_style="green", padding=(1, 2))
