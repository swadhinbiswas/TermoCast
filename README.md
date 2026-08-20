# 🌤️ TermoCast 1.0 — Advanced Terminal Dashboard
[![Visits Badge](https://badges.pufler.dev/visits/swadhinbiswas/TermoCast)](https://github.com/swadhinbiswas/TermoCast)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![Textual](https://img.shields.io/badge/TUI-Textual%208.x-green)](https://textual.textualize.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

> **Weather • News • Stocks • Crypto — in your terminal ⛅️**  
> A polished **Textual + Rich** TUI with headless CLI fallback. No API keys. Cached. Extensible.

![TermoCast Demo](https://raw.githubusercontent.com/swadhinbiswas/TermoCast/main/assets/demo.png)

---

## ✨ What's New in 1.0 (Complete Rewrite)

| Area | Before (0.1) | After (1.0) |
|---|---|---|
| **UI** | `print(wttr.in)` text | Full **Textual TUI** with tabs, search, help, live refresh |
| **Data** | Weather only, single city | **Weather** + **News** (HN + BBC RSS) + **Stocks** (Yahoo) + **Crypto** (CoinGecko) |
| **CLI** | `weather` (side-effect on import) | `termocast` + `weather` (Typer, 7 subcommands, JSON output) |
| **Config** | Hard-coded | `~/.config/termocast/config.json` + CLI `config` commands |
| **Caching** | None | TTL per domain (weather 10m, news 5m, stocks 1m, crypto 2m) with disk fallback |
| ** Packaging** | `usr/bin/weather.py` | `termocast/` package + backward-compat shim |

---

## 🏗️ Architecture

```
termocast/
├── __init__.py          # version 1.0.0
├── app.py               # Textual App (Header, TabbedContent, HelpScreen)
├── cli.py               # Typer CLI — tui + headless commands
├── config.py            # Config dataclass → ~/.config/termocast/config.json
├── constants.py         # API URLs, defaults, TTLs (all keyless)
├── services/
│   ├── base.py          # BaseService (retry, session, ServiceResult)
│   ├── weather.py       # wttr.in JSON + open-meteo fallback + geo
│   ├── news.py          # HN Algolia + BBC RSS (xml.etree parser)
│   ├── stocks.py        # Yahoo Finance chart + sparkline
│   └── crypto.py        # CoinGecko markets + sparkline
├── widgets/
│   ├── weather.py       # Rich Panel + Table (3-day forecast)
│   ├── news.py          # Rich Table (HackerNews/BBC)
│   ├── stocks.py        # Sparklines ▁▂▃▄▅▆▇█
│   └── crypto.py
├── screens/             # Tab panes (Vertical, not Screen — fixes deadlock)
│   ├── dashboard.py     # Overview (4 widgets, 4 thread workers, top imports)
│   ├── weather.py       # City input + geo button
│   ├── news.py          # Category Select + Search
│   ├── stocks.py        # Add/Reset watchlist
│   └── settings.py      # Edit & persist config
└── utils/
    ├── cache.py         # TTLCache (memory + JSON disk, @cached decorator)
    ├── geolocation.py   # geocoder → ip-api → ipinfo chain, cached
    └── formatters.py    # sparkline, currency, percent, date
```

**Key design decisions:**

- **No API keys** — wttr.in, HN Algolia, BBC RSS, Yahoo Finance, CoinGecko are all free-tier. Graceful fallback (open-meteo, legacy wttr text) + `ServiceResult(ok, data, error, cached, latency_ms)`.
- **No deadlock** — services use lazy `__getattr__` in `services/__init__.py` + top-level imports in screens; workers are `@work(thread=True)` with `call_from_thread`.
- **No `_render` clash** — widgets rename `_render` → `_build_panel` (Textual’s `Widget._render` is reserved).
- **Screens as Widgets** — `DashboardScreen(Vertical)` not `Screen` — TabPane expects Widgets; `HelpScreen(ModalScreen)` stays as true Screen.
- **Backward compat** — `weather` console_script now points to `termocast.cli:weather_entry` (Typer) but `usr/bin/weather.py:60` no longer auto-executes on import.
- **Caching** — `TTLCache` per domain with disk JSON at `~/.cache/termocast/*.json`; `cached` decorator for sync helpers.

---

## 🚀 Installation

### From Source (recommended)
```bash
git clone https://github.com/swadhinbiswas/TermoCast.git
cd TermoCast
pip install -r requirements.txt
pip install -e .   # editable, registers `termocast` + `weather`
```

### From PyPI
```bash
pip install termocast         # or pip3 install termocast
```

### Debian
```bash
dpkg-buildpackage -us -uc
sudo dpkg -i ../python3-termocast_1.0.0_all.deb
```

**Requirements:** Python 3.9+, `requests`, `geocoder`, `rich`, `typer`, `textual>=6`, `httpx`

---

## 🖥️ Usage

### TUI (default)
```bash
termocast                 # launch dashboard (auto-detect city)
termocast --city Tokyo    # override city for this session
termocast tui             # explicit
python -m termocast       # module
```

**TUI keys:** `Tab`/`Shift+Tab` tabs, `d` dashboard `w` weather `n` news `m` markets `s` settings, `r` refresh, `?` help, `q` quit.

### Headless CLI
```bash
# Weather
weather                   # backward-compat, auto-detect IP
termocast weather --city London
termocast weather --json
termocast weather --raw

# News
termocast news --category technology --source all --limit 10
termocast news --search "AI" --limit 5
termocast news --category world --source bbc

# Stocks (Yahoo, no key)
termocast stocks                  # watchlist
termocast stocks AAPL,MSFT,TSLA
termocast stocks --add NVDA,AMD
termocast stocks --remove TSLA
termocast stocks --list --json

# Crypto (CoinGecko, no key)
termocast crypto                  # watchlist
termocast crypto --top 10
termocast crypto bitcoin,ethereum --json

# Config
termocast config show
termocast config set --city "Dhaka" --stocks "AAPL,GOOGL" --crypto "bitcoin,solana"
termocast config reset
termocast config path
```

### Legacy
```bash
python usr/bin/weather.py   # still works, now delegates to service (no import side-effect)
```

---

## ⚙️ Configuration

`~/.config/termocast/config.json` (auto-created):

```json
{
  "city": null,
  "stocks": ["AAPL","GOOGL","MSFT","TSLA","NVDA","^GSPC","BTC-USD"],
  "crypto": ["bitcoin","ethereum","solana","binancecoin"],
  "news_category": "technology",
  "refresh_interval": 300,
  "units": "metric",
  "cache_ttl": {"weather":600,"news":300,"stocks":60,"crypto":120}
}
```

---

## 🔌 APIs (all keyless)

- **Weather:** `https://wttr.in/{city}?format=j1` → fallback `https://api.open-meteo.com/v1/forecast` + legacy `wttr.in` text slicing
- **News:** `https://hn.algolia.com/api/v1/search?tags=front_page` + `https://feeds.bbci.co.uk/news/{category}/rss.xml` (parsed via `xml.etree`)
- **Stocks:** `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}` + `spark` batch endpoint
- **Crypto:** `https://api.coingecko.com/api/v3/coins/markets`
- **Geo:** `geocoder.ip('me')` → `http://ip-api.com/json/` → `https://ipinfo.io/json`

---

## 🧪 Smoke Test

```bash
termocast weather --city London --json | jq .current
termocast news --limit 3
termocast stocks AAPL,MSFT --json
termocast crypto --top 5
python -c "from termocast.services.weather import WeatherService; print(WeatherService().fetch('London').ok)"
```

TUI pilot (headless):

```python
from termocast.app import TermoCastApp
from termocast.config import Config
import asyncio
async def p():
    async with TermoCastApp(Config(city="London")).run_test() as pilot:
        await pilot.pause()
        await pilot.press("w")
asyncio.run(p())
```

---

## 🤝 Thanks

- [@cubin](https://github.com/chubin) for **wttr.in**
- [Textualize](https://textual.textualize.io) for **Textual**
- Will McGugan for **Rich**

---

## 📄 License

MIT © 2024 Swadhin Biswas — see [LICENSE](./LICENSE)

## 👥 Contributors

[![Contributors Display](https://badges.pufler.dev/contributors/swadhinbiswas/TermoCast/?size=50&padding=5&perRow=10&bots=true)](https://github.com/swadhinbiswas/TermoCast)
