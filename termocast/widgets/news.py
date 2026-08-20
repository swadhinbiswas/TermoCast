"""News widget — ListView / DataTable hybrid."""

from __future__ import annotations

from textual.widgets import Static, DataTable, Label
from textual.containers import Vertical
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

class NewsWidget(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.articles: list[dict] = []

    def update_news(self, articles: list[dict] | None, error: str | None = None):
        if error:
            self.update(f"[red]News error: {error}[/red]")
            return
        if not articles:
            self.update("[yellow]No news available[/yellow]")
            return
        self.articles = articles
        self.update(self._build_panel(articles))

    def _build_panel(self, articles: list[dict]):
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1), expand=True)
        table.add_column("#", width=3, style="dim")
        table.add_column("Title", ratio=3, style="white", overflow="fold")
        table.add_column("Source", width=16, style="magenta")
        table.add_column("Meta", width=14, style="dim")

        for idx, a in enumerate(articles[:15], 1):
            title = a.get("title", "")[:78]
            src = a.get("source", "News")[:16]
            meta = ""
            if "points" in a:
                meta = f"▲{a.get('points',0)} 💬{a.get('num_comments',0)}"
            elif a.get("published"):
                meta = a.get("published", "")[:14]
            table.add_row(str(idx), title, src, meta)

        return Panel(table, title="[bold yellow]Latest News — Press Enter to open in browser[/]", border_style="yellow", padding=(1, 1))
