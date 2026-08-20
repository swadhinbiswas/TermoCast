"""Dashboard — overview with weather summary + news + markets."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Label, LoadingIndicator
from textual import work

from ..widgets import WeatherWidget, NewsWidget, StocksWidget, CryptoWidget
from ..config import Config
from ..services.weather import WeatherService
from ..services.news import NewsService
from ..services.stocks import StockService
from ..services.crypto import CryptoService


class DashboardScreen(Vertical):
    DEFAULT_CSS = """
    DashboardScreen {
        background: $surface;
    }
    #dash-scroll {
        padding: 1 2;
    }
    .dash-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin: 1 0;
    }
    """

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.weather_widget = WeatherWidget(id="dash-weather")
        self.news_widget = NewsWidget(id="dash-news")
        self.stocks_widget = StocksWidget(id="dash-stocks")
        self.crypto_widget = CryptoWidget(id="dash-crypto")

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Static(f"[bold cyan]TermoCast[/]  [dim]— Weather • News • Markets[/]   [yellow]r: refresh  q: quit  ?: help  tab: navigate[/]", classes="dash-title"),
            self.weather_widget,
            self.news_widget,
            self.stocks_widget,
            self.crypto_widget,
            id="dash-scroll",
        )

    def on_mount(self):
        self.refresh_all()

    def refresh_all(self):
        self.weather_widget.update("[dim]Loading weather…[/dim]")
        self.news_widget.update("[dim]Loading news…[/dim]")
        self.stocks_widget.update("[dim]Loading markets…[/dim]")
        self.crypto_widget.update("[dim]Loading crypto…[/dim]")
        self.load_weather()
        self.load_news()
        self.load_stocks()
        self.load_crypto()

    @work(thread=True)
    def load_weather(self):
        svc = WeatherService()
        res = svc.fetch(self.config.city)
        self.app.call_from_thread(self.weather_widget.update_weather, res.data if res.ok else None, res.error if not res.ok else None)

    @work(thread=True)
    def load_news(self):
        svc = NewsService()
        res = svc.fetch(category=self.config.news_category, limit=7)
        self.app.call_from_thread(self.news_widget.update_news, res.data if res.ok else None, res.error if not res.ok else None)

    @work(thread=True)
    def load_stocks(self):
        svc = StockService()
        res = svc.fetch_many(self.config.stocks[:6])
        self.app.call_from_thread(self.stocks_widget.update_stocks, res.data if res.ok else None, res.error if not res.ok else None)

    @work(thread=True)
    def load_crypto(self):
        svc = CryptoService()
        res = svc.fetch(self.config.crypto[:5])
        self.app.call_from_thread(self.crypto_widget.update_crypto, res.data if res.ok else None, res.error if not res.ok else None)
