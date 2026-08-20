"""Typer CLI — TUI + headless commands. Entry points: termocast, weather."""

from __future__ import annotations

import json
import sys
from typing import Optional, List
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from . import __version__
from .config import load_config, Config, get_config_path
from .constants import DEFAULT_STOCKS

app = typer.Typer(
    name="termocast",
    help="TermoCast — Weather • News • Markets in your terminal ⛅️",
    add_completion=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
)
console = Console()


def _version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]TermoCast[/] v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-V", help="Show version", callback=_version_callback, is_eager=True),
    city: Optional[str] = typer.Option(None, "--city", "-c", help="Override city for this run"),
):
    """Launch TUI if no subcommand given."""
    if ctx.invoked_subcommand is None:
        # Default: launch TUI (unless --help / --version)
        # Allow `weather` shim to pass through: if invoked as `weather`, do headless weather by default? keep TUI opt-in.
        # For `termocast` with no args -> TUI
        # For `weather` binary -> headless for backward compat, but allow --tui flag
        prog = Path(sys.argv[0]).name
        if prog == "weather" and city is None:
            # backward compat: headless weather if called as `weather` with no args
            # but we still support `weather --tui` to launch TUI
            # Check if any flag wants TUI
            if "--tui" in sys.argv or "--app" in sys.argv:
                from .app import run_app
                cfg = load_config()
                if city:
                    cfg.city = city
                run_app(cfg)
                raise typer.Exit()
            # else do quick headless
            _cmd_weather(city=None, json_out=False, raw=False)
            raise typer.Exit()
        # termocast no args -> TUI
        from .app import run_app
        cfg = load_config()
        if city:
            cfg.city = city
        run_app(cfg)


# ---------- weather ----------
@app.command("weather")
def _cmd_weather(
    city: Optional[str] = typer.Option(None, "--city", "-c", help="City (default: auto-detect)"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    raw: bool = typer.Option(False, "--raw", help="Raw wttr.in text (legacy)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
):
    """Show weather forecast (headless)."""
    from .services.weather import WeatherService
    from .utils.formatters import format_date

    svc = WeatherService()
    res = svc.fetch(city, force=no_cache)
    if not res.ok:
        console.print(f"[red]Error:[/] {res.error}")
        raise typer.Exit(1)

    data = res.data
    if json_out:
        console.print_json(data=json.dumps(data, indent=2, default=str))
        return

    if raw and "raw_text" in data:
        console.print(data["raw_text"])
        return
    if raw:
        # fallback: print text via wttr raw endpoint
        import requests
        c = city or data.get("requested_city") or "London"
        try:
            t = requests.get(f"https://wttr.in/{c}", timeout=6, verify=False).text
            # same legacy slicing
            console.print(t[:-127] if len(t) > 200 else t)
        except Exception as e:
            console.print(f"[red]Raw fetch failed:[/] {e}")
        return

    # Rich panel rendering (headless)
    cur = data.get("current", {})
    city_disp = data.get("city") or data.get("requested_city")
    desc = cur.get("weatherDesc", "")
    # header
    console.print(Panel(f"[bold green]{city_disp}[/] — {desc}  [dim]{data.get('source','')}{' (cached)' if res.cached else ''}[/]", style="green", title="TermoCast Weather ⛅️", title_align="center"))

    if cur.get("temp_C"):
        t = Table(show_header=False, box=None, padding=(0,1))
        t.add_column("k", style="cyan bold")
        t.add_column("v")
        t.add_row("Temp", f"{cur.get('temp_C')}°C / {cur.get('temp_F')}°F (feels {cur.get('feelsLikeC','—')}°C)")
        t.add_row("Humidity", f"{cur.get('humidity','—')}%")
        t.add_row("Wind", f"{cur.get('windspeedKmph','—')} km/h {cur.get('winddir16Point','')}")
        t.add_row("Pressure", f"{cur.get('pressure','—')} hPa")
        console.print(t)

    fc = data.get("forecast", [])
    if fc:
        ft = Table(title="Forecast", show_header=True, header_style="bold magenta")
        ft.add_column("Date", style="cyan")
        ft.add_column("Max", justify="right", style="red")
        ft.add_column("Min", justify="right", style="blue")
        ft.add_column("Condition")
        for d in fc:
            ft.add_row(format_date(d.get("date")), f"{d.get('maxtempC','—')}°C", f"{d.get('mintempC','—')}°C", d.get("desc","")[:40])
        console.print(ft)

    if "raw_text" in data:
        console.print(Panel(data["raw_text"][:2000], title="Raw wttr.in", border_style="dim"))


# ---------- news ----------
@app.command("news")
def _cmd_news(
    category: str = typer.Option("technology", "--category", "-k", help="world|technology|business|science"),
    source: str = typer.Option("all", "--source", "-s", help="hn|bbc|all"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of articles"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    search: Optional[str] = typer.Option(None, "--search", "-q", help="Search HackerNews"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
):
    """Show latest news."""
    from .services.news import NewsService
    svc = NewsService()
    if search:
        res = svc.search(search, limit=limit)
    else:
        res = svc.fetch(category=category, source=source, limit=limit, force=no_cache)
    if not res.ok:
        console.print(f"[red]Error:[/] {res.error}")
        raise typer.Exit(1)
    if json_out:
        console.print_json(data=json.dumps(res.data, indent=2, default=str))
        return
    table = Table(title=f"News — {category} ({source}){' [search: '+search+']' if search else ''}", show_header=True, header_style="bold yellow")
    table.add_column("#", width=3)
    table.add_column("Title", ratio=3, overflow="fold")
    table.add_column("Source", width=16)
    table.add_column("Meta", width=18)
    for i, a in enumerate(res.data, 1):
        meta = f"▲{a.get('points',0)} 💬{a.get('num_comments',0)}" if "points" in a else (a.get("published","")[:16] or a.get("description","")[:18])
        table.add_row(str(i), a.get("title","")[:90], a.get("source","")[:16], meta)
        if a.get("url"):
            table.add_row("", f"[dim link={a['url']}]{a['url'][:60]}[/]", "", "")
    console.print(table)
    if res.cached:
        console.print("[dim](cached)[/dim]")


# ---------- stocks ----------
@app.command("stocks")
def _cmd_stocks(
    symbols: Optional[str] = typer.Argument(None, help="Comma-separated symbols (e.g. AAPL,MSFT) or empty for watchlist"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    add: Optional[str] = typer.Option(None, "--add", help="Add symbol(s) to watchlist (comma separated)"),
    remove: Optional[str] = typer.Option(None, "--remove", help="Remove symbol from watchlist"),
    list_watchlist: bool = typer.Option(False, "--list", help="List watchlist"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
):
    """Show stock quotes (Yahoo Finance, no key)."""
    from .services.stocks import StockService
    cfg = load_config()
    svc = StockService()

    if list_watchlist:
        console.print(f"[bold]Watchlist:[/] {', '.join(cfg.stocks)}")
        return
    if add:
        for s in [x.strip().upper() for x in add.split(",") if x.strip()]:
            if s not in cfg.stocks:
                cfg.stocks.append(s)
        cfg.save()
        console.print(f"[green]Added:[/] {add} → {', '.join(cfg.stocks)}")
        return
    if remove:
        r = remove.strip().upper()
        if r in cfg.stocks:
            cfg.stocks.remove(r)
            cfg.save()
            console.print(f"[yellow]Removed {r}[/] → {', '.join(cfg.stocks)}")
        else:
            console.print(f"[red]{r} not in watchlist[/]")
        return

    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else cfg.stocks
    res = svc.fetch_many(syms, force=no_cache)
    if not res.ok:
        console.print(f"[red]Error:[/] {res.error}")
        raise typer.Exit(1)
    if json_out:
        console.print_json(data=json.dumps(res.data, indent=2, default=str))
        return

    from .utils.formatters import format_currency, format_percent
    table = Table(title=f"Stocks — Yahoo Finance{' (cached)' if res.cached else ''}", show_header=True, header_style="bold green")
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Name", overflow="fold")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Spark", width=14)
    table.add_column("Range")
    for s in res.data:
        price = s.get("price")
        curr = s.get("currency","USD")
        ch = s.get("change",0)
        pct = s.get("changePercent",0)
        price_s = format_currency(price, curr) if price is not None else "—"
        ch_s = f"{format_currency(ch,curr)} ({format_percent(pct)})"
        if pct and pct > 0:
            ch_s = f"[green]{ch_s}[/green]"
        elif pct and pct < 0:
            ch_s = f"[red]{ch_s}[/red]"
        table.add_row(s.get("symbol"), (s.get("shortName") or "")[:28], price_s, ch_s, s.get("spark","—"), f"{s.get('dayLow','—')}–{s.get('dayHigh','—')}")
    console.print(table)
    if res.error:
        console.print(f"[yellow]Partial errors: {res.error}[/yellow]")


# ---------- crypto ----------
@app.command("crypto")
def _cmd_crypto(
    coins: Optional[str] = typer.Argument(None, help="Comma-separated ids e.g. bitcoin,ethereum or empty for watchlist"),
    top: int = typer.Option(0, "--top", help="Show top N by market cap (e.g. --top 10)"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
):
    """Show crypto prices (CoinGecko, no key)."""
    from .services.crypto import CryptoService
    cfg = load_config()
    svc = CryptoService()
    if top:
        res = svc.top(per_page=top, force=no_cache)
    else:
        ids = [c.strip().lower() for c in coins.split(",") if c.strip()] if coins else cfg.crypto
        res = svc.fetch(ids=ids, force=no_cache)
    if not res.ok:
        console.print(f"[red]Error:[/] {res.error}")
        raise typer.Exit(1)
    if json_out:
        console.print_json(data=json.dumps(res.data, indent=2, default=str))
        return
    from .utils.formatters import format_currency, format_percent
    title = f"Crypto — CoinGecko {'(cached)' if res.cached else ''}"
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("#", width=3)
    table.add_column("Coin", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("24h", justify="right")
    table.add_column("7d", justify="right")
    table.add_column("Spark")
    for c in res.data:
        ch24 = c.get("change_24h")
        ch7 = c.get("change_7d")
        ch24_s = format_percent(ch24) if ch24 is not None else "—"
        ch7_s = format_percent(ch7) if ch7 is not None else "—"
        if ch24 and ch24 > 0: ch24_s = f"[green]{ch24_s}[/green]"
        elif ch24 and ch24 < 0: ch24_s = f"[red]{ch24_s}[/red]"
        if ch7 and ch7 > 0: ch7_s = f"[green]{ch7_s}[/green]"
        elif ch7 and ch7 < 0: ch7_s = f"[red]{ch7_s}[/red]"
        table.add_row(str(c.get("rank") or ""), f"{c.get('symbol','')} {c.get('name','')[:12]}", format_currency(c.get("price"),"USD"), ch24_s, ch7_s, c.get("spark","—"))
    console.print(table)


# ---------- config ----------
config_app = typer.Typer(help="Manage config (~/.config/termocast/config.json)")
app.add_typer(config_app, name="config")

@config_app.command("show")
def _cfg_show(json_out: bool = typer.Option(False, "--json", help="JSON output")):
    cfg = load_config()
    if json_out:
        console.print_json(data=json.dumps(cfg.__dict__, indent=2, default=str))
    else:
        console.print(Panel(f"[bold cyan]Config:[/] {get_config_path()}\n\n{json.dumps(cfg.__dict__, indent=2)}", title="TermoCast Config", border_style="blue"))
        console.print(f"[dim]Edit: {get_config_path()}[/dim]")

@config_app.command("set")
def _cfg_set(
    city: Optional[str] = typer.Option(None, "--city", help="Set city (empty for auto)"),
    stocks: Optional[str] = typer.Option(None, "--stocks", help="Comma-separated stocks"),
    crypto: Optional[str] = typer.Option(None, "--crypto", help="Comma-separated crypto ids"),
    category: Optional[str] = typer.Option(None, "--category", help="News category"),
):
    cfg = load_config()
    if city is not None:
        cfg.city = city.strip() or None
    if stocks is not None:
        cfg.stocks = [s.strip().upper() for s in stocks.split(",") if s.strip()]
    if crypto is not None:
        cfg.crypto = [c.strip().lower() for c in crypto.split(",") if c.strip()]
    if category is not None:
        cfg.news_category = category
    cfg.save()
    console.print("[green]Config saved[/]")
    _cfg_show(json_out=False)

@config_app.command("reset")
def _cfg_reset():
    cfg = Config()
    cfg.save()
    console.print("[yellow]Config reset to defaults[/]")
    _cfg_show(json_out=False)

@config_app.command("path")
def _cfg_path():
    console.print(str(get_config_path()))


# ---------- tui ----------
@app.command("tui")
def _cmd_tui(
    city: Optional[str] = typer.Option(None, "--city", "-c", help="Override city for TUI session"),
):
    """Launch the Textual TUI explicitly."""
    from .app import run_app
    cfg = load_config()
    if city:
        cfg.city = city
    run_app(cfg)


@app.command("dashboard")
def _cmd_dashboard(city: Optional[str] = typer.Option(None, "--city", "-c")):
    """Alias for tui."""
    _cmd_tui(city)


# Backwards-compat shim: `weather` entry point should still work via termocast.cli:app
def weather_entry():
    """Called by console_script `weather` — delegates to Typer with headless default."""
    # Re-use main logic but force headless if no explicit --tui
    sys.argv[0] = "weather"
    app()

if __name__ == "__main__":
    app()
