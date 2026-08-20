"""Settings screen — edit config."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Input, Button, Label, Static, Select
from textual import work

from ..config import Config
from ..constants import CONFIG_FILE


class SettingsScreen(Vertical):
    DEFAULT_CSS = """
    SettingsScreen { background: $surface; }
    #settings-scroll { padding: 1 2; }
    .setting-label { width: 18; color: $accent; text-style: bold; }
    .setting-row { height: 3; margin: 1 0; }
    """

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Static("[bold cyan]Settings[/]  [dim]— persisted to ~/.config/termocast/config.json[/]", classes="title"),
            Horizontal(Label("City", classes="setting-label"), Input(value=self.config.city or "", placeholder="auto-detect if empty", id="city"), id="row-city", classes="setting-row"),
            Horizontal(Label("Stocks (csv)", classes="setting-label"), Input(value=",".join(self.config.stocks), id="stocks"), classes="setting-row"),
            Horizontal(Label("Crypto (csv)", classes="setting-label"), Input(value=",".join(self.config.crypto), id="crypto"), classes="setting-row"),
            Horizontal(Label("News category", classes="setting-label"), Select([("technology","technology"),("world","world"),("business","business"),("science","science")], value=self.config.news_category, id="news-cat", allow_blank=False), classes="setting-row"),
            Horizontal(Label("Refresh (sec)", classes="setting-label"), Input(value=str(self.config.refresh_interval), id="refresh"), classes="setting-row"),
            Horizontal(Label("Units", classes="setting-label"), Select([("metric","metric"),("imperial","imperial")], value=self.config.units, id="units", allow_blank=False), classes="setting-row"),
            Horizontal(Button("Save", variant="primary", id="save"), Button("Reset defaults", variant="error", id="reset"), Button("Back", variant="default", id="back"), classes="setting-row"),
            Static(f"[dim]Config file: {CONFIG_FILE}[/]", id="config-path"),
            Static(self._about_text(), id="about"),
            id="settings-scroll",
        )

    def _about_text(self):
        return (
            "[bold]TermoCast 1.0[/] — Weather • News • Markets TUI\n"
            "[dim]Built with Textual + Rich • Data: wttr.in, HN Algolia, BBC RSS, Yahoo Finance, CoinGecko[/]\n"
            "[dim]All APIs are keyless & free-tier, cached locally (TTL per domain)[/]\n"
            "[dim]Keys: Tab/Shift+Tab navigate • r refresh • q quit • ? help • d dashboard • w weather • n news • m markets • s settings[/]"
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            self._save()
        elif event.button.id == "reset":
            self.config = Config()
            self.config.save()
            self.app.notify("Reset to defaults — restart tab to see changes", timeout=3)
            # re-compose: update inputs
            self.query_one("#city", Input).value = self.config.city or ""
            self.query_one("#stocks", Input).value = ",".join(self.config.stocks)
            self.query_one("#crypto", Input).value = ",".join(self.config.crypto)
        elif event.button.id == "back":
            # back = go to dashboard tab
            try:
                self.app.query_one("#main-tabs").active = "dashboard"
            except Exception:
                pass

    def _save(self):
        try:
            city = self.query_one("#city", Input).value.strip() or None
            stocks = [s.strip().upper() for s in self.query_one("#stocks", Input).value.split(",") if s.strip()]
            crypto = [c.strip().lower() for c in self.query_one("#crypto", Input).value.split(",") if c.strip()]
            news_cat = self.query_one("#news-cat", Select).value
            refresh = int(self.query_one("#refresh", Input).value.strip() or "300")
            units = self.query_one("#units", Select).value

            self.config.city = city
            if stocks:
                self.config.stocks = stocks
            if crypto:
                self.config.crypto = crypto
            self.config.news_category = str(news_cat)
            self.config.refresh_interval = refresh
            self.config.units = str(units)
            self.config.save()
            self.app.notify("Settings saved ✓", timeout=2)
        except Exception as e:
            self.app.notify(f"Save failed: {e}", severity="error")
