"""Formatting helpers for TUI & CLI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence


def sparkline(values: Sequence[float]) -> str:
    """Tiny sparkline using block chars ▁▂▃▄▅▆▇█."""
    if not values:
        return ""
    chars = "▁▂▃▄▅▆▇█"
    mn, mx = min(values), max(values)
    if mx == mn:
        return chars[len(chars)//2] * len(values)
    out = ""
    for v in values:
        idx = int((v - mn) / (mx - mn) * (len(chars) - 1))
        out += chars[idx]
    return out


def format_currency(value: float, currency: str = "USD") -> str:
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}
    sym = symbols.get(currency.upper(), currency + " ")
    if value is None:
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"{sym}{value/1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{sym}{value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{sym}{value:,.2f}"
    return f"{sym}{value:,.2f}"


def format_percent(value: float) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def truncate(text: str, max_len: int = 80) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def format_time(ts: int | float | None) -> str:
    if not ts:
        return "—"
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
        return dt.strftime("%H:%M")
    except Exception:
        return str(ts)


def format_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        # wttr.in date format YYYY-MM-DD
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%a %d %b")
    except Exception:
        return iso
