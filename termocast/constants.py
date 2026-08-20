"""Constants and defaults for TermoCast."""

from pathlib import Path

# Branding
APP_NAME = "TermoCast"
APP_TAGLINE = "Weather • News • Markets — in your terminal ⛅️"
APP_SUBTITLE = "by @swadhinbiswas"

# Paths
CONFIG_DIR = Path.home() / ".config" / "termocast"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = Path.home() / ".cache" / "termocast"

# API endpoints (all keyless / free)
WTTR_URL = "https://wttr.in/{city}?format=j1"  # JSON forecast, no key
WTTR_TEXT_URL = "https://wttr.in/{city}?format=%C+%t+%w+%h"  # fallback
IP_API_URL = "http://ip-api.com/json/"  # fallback geolocation (no key, 45 req/min)
GEOCODER_FALLBACK = True

# News — keyless
HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search?tags=front_page"
HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
RSS_FEEDS = {
    "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
}

# Stocks / Markets — Yahoo Finance (no key)
YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1mo"
YAHOO_QUOTE_SIMPLE = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=price"
# Alternative lightweight quote via Yahoo chart meta
YAHOO_SPARK_URL = "https://query1.finance.yahoo.com/v8/finance/spark?symbols={symbols}&range=1d&interval=5m"

# Crypto — CoinGecko (no key, rate-limited)
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_PING = "https://api.coingecko.com/api/v3/ping"

# Defaults
DEFAULT_CITY = None  # auto-detect
DEFAULT_STOCKS = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "^GSPC", "BTC-USD"]
DEFAULT_CRYPTO = ["bitcoin", "ethereum", "solana", "binancecoin"]
DEFAULT_NEWS_CATEGORY = "technology"
DEFAULT_REFRESH_INTERVAL = 300  # seconds
DEFAULT_THEME = "termocast-dark"

# UI
SPARK_CHARS = "▁▂▃▄▅▆▇█"
WEATHER_EMOJI = {
    "Sunny": "☀️",
    "Clear": "🌙",
    "Partly cloudy": "⛅",
    "Cloudy": "☁️",
    "Overcast": "☁️",
    "Mist": "🌫️",
    "Patchy rain": "🌦️",
    "Light rain": "🌧️",
    "Moderate rain": "🌧️",
    "Heavy rain": "⛈️",
    "Thundery": "⛈️",
    "Snow": "❄️",
    "Fog": "🌫️",
}

CACHE_TTL = {
    "weather": 600,   # 10 min
    "news": 300,      # 5 min
    "stocks": 60,     # 1 min
    "crypto": 120,    # 2 min
    "geolocation": 3600,
}
