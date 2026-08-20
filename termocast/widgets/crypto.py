"""Crypto widget."""

from __future__ import annotations

from textual.widgets import Static
from rich.panel import Panel
from rich.table import Table

from ..utils.formatters import format_currency, format_percent


class CryptoWidget(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_crypto(self, coins: list[dict] | None, error: str | None = None):
        if error:
            self.update(f"[red]Crypto error: {error}[/red]")
            return
        if not coins:
            self.update("[yellow]No crypto data[/yellow]")
            return
        self.update(self._build_panel(coins))

    def _build_panel(self, coins: list[dict]):
        table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 1), expand=True)
        table.add_column("#", width=3, style="dim")
        table.add_column("Coin", width=14, style="bold cyan")
        table.add_column("Price (USD)", width=14, justify="right")
        table.add_column("24h", width=10, justify="right")
        table.add_column("7d", width=10, justify="right")
        table.add_column("Spark 7d", width=16, style="dim")

        for c in coins[:10]:
            rank = str(c.get("rank") or "")
            name = f"{c.get('symbol','')} {c.get('name','')[:10]}"
            price = c.get("price")
            ch24 = c.get("change_24h")
            ch7 = c.get("change_7d")
            spark = c.get("spark", "")

            price_str = format_currency(price, "USD") if price is not None else "—"
            ch24_str = format_percent(ch24) if ch24 is not None else "—"
            ch7_str = format_percent(ch7) if ch7 is not None else "—"
            if ch24 and ch24 > 0:
                ch24_str = f"[green]{ch24_str}[/green]"
            elif ch24 and ch24 < 0:
                ch24_str = f"[red]{ch24_str}[/red]"
            if ch7 and ch7 > 0:
                ch7_str = f"[green]{ch7_str}[/green]"
            elif ch7 and ch7 < 0:
                ch7_str = f"[red]{ch7_str}[/red]"

            table.add_row(rank, name.strip(), price_str, ch24_str, ch7_str, spark or "—")

        return Panel(table, title="[bold magenta]Crypto — CoinGecko (free) — Top by market cap[/]", border_style="magenta", padding=(1, 1))
