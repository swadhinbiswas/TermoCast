"""News screen with category & source selector."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import Button, Static, Select, Input, Label
from textual import work
import webbrowser

from ..widgets import NewsWidget
from ..config import Config
from ..services.news import NewsService


class NewsScreen(Vertical):
    DEFAULT_CSS = """
    NewsScreen { background: $surface; }
    #news-controls { height: 3; margin: 1 2; }
    #news-scroll { padding: 1 2; }
    """

    CATEGORIES = [("Technology", "technology"), ("World", "world"), ("Business", "business"), ("Science", "science")]

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.widget = NewsWidget()
        self.current_category = config.news_category

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Select([(c[0], c[1]) for c in self.CATEGORIES], value=self.current_category, id="cat-select", allow_blank=False),
            Button("HackerNews", id="btn-hn", variant="primary"),
            Button("BBC RSS", id="btn-bbc", variant="default"),
            Button("All", id="btn-all", variant="success"),
            Input(placeholder="Search HackerNews...", id="search-input", classes="search"),
            Button("Search", id="btn-search", variant="warning"),
            id="news-controls",
        )
        yield VerticalScroll(self.widget, id="news-scroll")

    def on_mount(self):
        self._load(self.current_category, "all")

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "cat-select":
            self.current_category = str(event.value)
            self._load(self.current_category, "all")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-hn":
            self._load(self.current_category, "hn")
        elif event.button.id == "btn-bbc":
            self._load(self.current_category, "bbc")
        elif event.button.id == "btn-all":
            self._load(self.current_category, "all")
        elif event.button.id == "btn-search":
            q = self.query_one("#search-input", Input).value.strip()
            if q:
                self._search(q)

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "search-input":
            q = event.value.strip()
            if q:
                self._search(q)

    def _load(self, category: str, source: str):
        self.widget.update(f"[dim]Loading {source} news ({category})…[/dim]")
        self._do_load(category, source)

    @work(thread=True)
    def _do_load(self, category: str, source: str):
        svc = NewsService()
        res = svc.fetch(category=category, source=source, limit=15, force=True)
        self.app.call_from_thread(self.widget.update_news, res.data if res.ok else None, res.error if not res.ok else None)

    def _search(self, query: str):
        self.widget.update(f"[dim]Searching '{query}'…[/dim]")
        self._do_search(query)

    @work(thread=True)
    def _do_search(self, query: str):
        svc = NewsService()
        res = svc.search(query)
        self.app.call_from_thread(self.widget.update_news, res.data if res.ok else None, res.error if not res.ok else None)
