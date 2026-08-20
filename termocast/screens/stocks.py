"""Markets screen — stocks + crypto."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import Input, Button, Static, Label
from textual import work

from ..widgets import StocksWidget, CryptoWidget
from ..config import Config
from ..services.stocks import StockService
from ..services.crypto import CryptoService
from ..constants import DEFAULT_STOCKS


class MarketsScreen(Vertical):
    DEFAULT_CSS = """
    MarketsScreen { background: $surface; }
    #markets-controls { height: 3; margin: 1 2; }
    #markets-scroll { padding: 1 2; }
    """

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.stocks_widget = StocksWidget()
        self.crypto_widget = CryptoWidget()

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Input(placeholder="Add symbol e.g. AAPL, TSLA, NVDA  (comma separated)", id="symbol-input"),
            Button("Add", variant="primary", id="add-btn"),
            Button("Reset", variant="default", id="reset-btn"),
            Button("Refresh", variant="success", id="refresh-btn"),
            id="markets-controls",
        )
        yield VerticalScroll(
            self.stocks_widget,
            Static(""),
            self.crypto_widget,
            id="markets-scroll",
        )

    def on_mount(self):
        self.refresh_all()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "add-btn":
            inp = self.query_one("#symbol-input", Input).value.strip()
            if inp:
                symbols = [s.strip().upper() for s in inp.split(",") if s.strip()]
                for s in symbols:
                    if s not in self.config.stocks:
                        self.config.stocks.append(s)
                self.config.save()
                self.query_one("#symbol-input", Input).value = ""
                self.refresh_all()
        elif event.button.id == "reset-btn":
            self.config.stocks = list(DEFAULT_STOCKS)
            self.config.save()
            self.refresh_all()
        elif event.button.id == "refresh-btn":
            self.refresh_all()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "symbol-input":
            self.on_button_pressed(Button.Pressed(Button("Add", id="add-btn")))

    def refresh_all(self):
        self.stocks_widget.update("[dim]Loading stocks…[/dim]")
        self.crypto_widget.update("[dim]Loading crypto…[/dim]")
        self._load_stocks()
        self._load_crypto()

    @work(thread=True)
    def _load_stocks(self):
        svc = StockService()
        res = svc.fetch_many(self.config.stocks, force=True)
        self.app.call_from_thread(self.stocks_widget.update_stocks, res.data if res.ok else None, res.error if not res.ok else None)

    @work(thread=True)
    def _load_crypto(self):
        svc = CryptoService()
        res = svc.fetch(self.config.crypto, force=True)
        self.app.call_from_thread(self.crypto_widget.update_crypto, res.data if res.ok else None, res.error if not res.ok else None)
