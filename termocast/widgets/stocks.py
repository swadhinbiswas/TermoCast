"""Stocks widget — DataTable with sparklines."""

from __future__ import annotations

from textual.widgets import Static
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..utils.formatters import format_currency, format_percent


class StocksWidget(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_stocks(self, stocks: list[dict] | None, error: str | None = None):
        if error:
            self.update(f"[red]Stocks error: {error}[/red]")
            return
        if not stocks:
            self.update("[yellow]No market data[/yellow]")
            return
        self.update(self._build_panel(stocks))

    def _build_panel(self, stocks: list[dict]):
        table = Table(show_header=True, header_style="bold green", box=None, padding=(0, 1), expand=True)
        table.add_column("Symbol", width=9, style="bold cyan")
        table.add_column("Name", ratio=2, style="white", overflow="fold")
        table.add_column("Price", width=12, justify="right")
        table.add_column("Change", width=12, justify="right")
        table.add_column("Spark (30d)", width=16, style="dim")
        table.add_column("Range", width=18, style="dim")

        for s in stocks[:10]:
            sym = s.get("symbol", "")
            name = (s.get("shortName") or sym)[:22]
            price = s.get("price")
            curr = s.get("currency", "USD")
            change = s.get("change", 0)
            pct = s.get("changePercent", 0)
            spark = s.get("spark", "")

            price_str = format_currency(price, curr) if price is not None else "—"
            ch_str = f"{format_currency(change, curr)} ({format_percent(pct)})" if price is not None else "—"
            # color
            if pct and pct > 0:
                ch_str = f"[green]{ch_str}[/green]"
            elif pct and pct < 0:
                ch_str = f"[red]{ch_str}[/red]"

            lo = s.get("dayLow")
            hi = s.get("dayHigh")
            rng = f"{lo:.2f}–{hi:.2f}" if lo and hi else "—"

            table.add_row(sym, name, price_str, ch_str, spark or "—", rng)

        return Panel(table, title="[bold green]Markets — Yahoo Finance (no key) — r to refresh[/]", border_style="green", padding=(1, 1))
