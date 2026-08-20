"""Dedicated weather screen with city input."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Input, Button, Static, Label
from textual import work

from ..widgets import WeatherWidget
from ..config import Config
from ..services.weather import WeatherService


class WeatherScreen(Vertical):
    DEFAULT_CSS = """
    WeatherScreen { background: $surface; }
    #weather-controls { height: 3; margin: 1 2; }
    #city-input { width: 1fr; margin-right: 1; }
    #weather-scroll { padding: 1 2; }
    """

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.widget = WeatherWidget()

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Input(placeholder=f"City (current: {self.config.city or 'auto-detect'})", id="city-input"),
            Button("Search", variant="primary", id="search-btn"),
            Button("Use my location", variant="default", id="geo-btn"),
            id="weather-controls",
        )
        yield VerticalScroll(self.widget, id="weather-scroll")

    def on_mount(self):
        self.fetch(self.config.city)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "search-btn":
            city = self.query_one("#city-input", Input).value.strip()
            if city:
                self.fetch(city)
        elif event.button.id == "geo-btn":
            self.query_one("#city-input", Input).value = ""
            self.fetch(None)

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "city-input":
            self.fetch(event.value.strip() or None)

    def fetch(self, city: str | None):
        self.widget.update("[dim]Fetching weather…[/dim]")
        self._load(city)

    @work(thread=True)
    def _load(self, city: str | None):
        svc = WeatherService()
        res = svc.fetch(city, force=True)
        self.app.call_from_thread(self.widget.update_weather, res.data if res.ok else None, res.error if not res.ok else None)
