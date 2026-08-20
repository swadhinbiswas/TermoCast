"""TermoCast TUI — Textual App with tabs, command palette, help."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Label
from textual.binding import Binding
from textual.screen import ModalScreen

from .config import Config, load_config
from .constants import APP_NAME, APP_TAGLINE
from .screens.dashboard import DashboardScreen
from .screens.weather import WeatherScreen
from .screens.news import NewsScreen
from .screens.stocks import MarketsScreen
from .screens.settings import SettingsScreen


class HelpScreen(ModalScreen):
    DEFAULT_CSS = """
    HelpScreen { align: center middle; }
    #help-box { width: 70; height: auto; padding: 1 2; background: $surface; border: thick $primary; }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                "[bold cyan]TermoCast — Help[/]\n\n"
                "[bold]Navigation[/]\n"
                "  Tab / Shift+Tab  → switch tabs\n"
                "  d  → Dashboard   w → Weather   n → News   m → Markets   s → Settings\n"
                "  q  → Quit        ? → This help   r → Refresh current tab\n\n"
                "[bold]Dashboard[/]\n"
                "  Shows weather + top news + markets overview (auto-refresh)\n\n"
                "[bold]Weather[/]\n"
                "  Type city + Enter / Search. ‘Use my location’ → IP geolocation\n"
                "  Data: wttr.in JSON (fallback open-meteo) — no API key\n\n"
                "[bold]News[/]\n"
                "  Categories: Tech/World/Business/Science  Sources: HN Algolia + BBC RSS\n"
                "  Use Search box for HN query\n\n"
                "[bold]Markets[/]\n"
                "  Stocks via Yahoo Finance chart API (no key) + sparklines\n"
                "  Crypto via CoinGecko (free) • Add symbols comma-separated (e.g. AAPL, NVDA)\n\n"
                "[bold]Settings[/]\n"
                "  Edit city, watchlists, refresh interval → Save (persisted to ~/.config/termocast/config.json)\n\n"
                "[dim]Press any key or Esc to close[/]",
                id="help-box",
            )
        )

    def on_key(self, event):
        self.dismiss()


class TermoCastApp(App):
    TITLE = APP_NAME
    SUB_TITLE = APP_TAGLINE
    CSS = """
    Header { background: $primary; }
    Footer { background: $primary; }
    TabbedContent { background: $surface; }
    Tabs { background: $surface; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "tab_dashboard", "Dashboard", show=False),
        Binding("w", "tab_weather", "Weather", show=False),
        Binding("n", "tab_news", "News", show=False),
        Binding("m", "tab_markets", "Markets", show=False),
        Binding("s", "tab_settings", "Settings", show=False),
    ]

    def __init__(self, config: Config | None = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or load_config()
        self._tabbed: TabbedContent | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="dashboard", id="main-tabs"):
            with TabPane("📊 Dashboard", id="dashboard"):
                yield DashboardScreen(self.config, id="dash-screen")
            with TabPane("⛅ Weather", id="weather"):
                yield WeatherScreen(self.config, id="weather-screen")
            with TabPane("📰 News", id="news"):
                yield NewsScreen(self.config, id="news-screen")
            with TabPane("📈 Markets", id="markets"):
                yield MarketsScreen(self.config, id="markets-screen")
            with TabPane("⚙️ Settings", id="settings"):
                yield SettingsScreen(self.config, id="settings-screen")
        yield Footer()

    def on_mount(self):
        self._tabbed = self.query_one("#main-tabs", TabbedContent)

    def action_help(self):
        self.push_screen(HelpScreen())

    def action_refresh(self):
        active = self._tabbed.active if self._tabbed else None
        self.notify(f"Refreshing {active}…", timeout=1.5)
        # delegate to screen's refresh method if exists
        try:
            pane = self.query_one(f"#{active}", TabPane)
            # find child screen
            for child in pane.walk_children():
                if hasattr(child, "refresh_all"):
                    child.refresh_all()
                    return
                if hasattr(child, "fetch"):
                    child.fetch(self.config.city)
                    return
                if hasattr(child, "_load"):
                    # fallback
                    pass
        except Exception:
            pass
        # brute: re-mount dashboard
        self.notify("Refresh triggered", timeout=1)

    def action_tab_dashboard(self):
        if self._tabbed: self._tabbed.active = "dashboard"
    def action_tab_weather(self):
        if self._tabbed: self._tabbed.active = "weather"
    def action_tab_news(self):
        if self._tabbed: self._tabbed.active = "news"
    def action_tab_markets(self):
        if self._tabbed: self._tabbed.active = "markets"
    def action_tab_settings(self):
        if self._tabbed: self._tabbed.active = "settings"


def run_app(config: Config | None = None):
    app = TermoCastApp(config=config)
    app.run()
