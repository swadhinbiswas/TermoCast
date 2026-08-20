"""Lazy exports to avoid import deadlocks in Textual thread workers."""

__all__ = ["WeatherService", "get_weather", "NewsService", "get_news", "StockService", "get_stocks", "CryptoService", "get_crypto"]

def __getattr__(name):
    if name == "WeatherService" or name == "get_weather":
        from .weather import WeatherService, get_weather
        return WeatherService if name == "WeatherService" else get_weather
    if name == "NewsService" or name == "get_news":
        from .news import NewsService, get_news
        return NewsService if name == "NewsService" else get_news
    if name == "StockService" or name == "get_stocks":
        from .stocks import StockService, get_stocks
        return StockService if name == "StockService" else get_stocks
    if name == "CryptoService" or name == "get_crypto":
        from .crypto import CryptoService, get_crypto
        return CryptoService if name == "CryptoService" else get_crypto
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
