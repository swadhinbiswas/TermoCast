def test_import_termocast():
    import termocast
    assert termocast.__version__ == "1.0.0"

def test_import_services():
    from termocast.services.weather import WeatherService
    from termocast.services.news import NewsService
    from termocast.services.stocks import StockService
    from termocast.services.crypto import CryptoService
    assert WeatherService
    assert NewsService
    assert StockService
    assert CryptoService

def test_config_load():
    from termocast.config import load_config
    cfg = load_config()
    assert cfg.stocks
    assert cfg.crypto

def test_formatters():
    from termocast.utils.formatters import sparkline, format_currency, format_percent
    assert sparkline([1,2,3]) == "▁▅█" or len(sparkline([1,2,3])) == 3
    assert "$" in format_currency(1234.5, "USD")
    assert "%" in format_percent(1.23)

def test_cli_help():
    from termocast.cli import app
    assert app

def test_widgets():
    from termocast.widgets import WeatherWidget, NewsWidget, StocksWidget, CryptoWidget
    assert WeatherWidget
    assert NewsWidget
    assert StocksWidget
    assert CryptoWidget

def test_no_import_side_effect():
    # usr/bin/weather should not auto-run on import
    import usr.bin.weather as w
    assert hasattr(w, "weather")
    assert hasattr(w, "findcity")

def test_tui_app_import():
    from termocast.app import TermoCastApp
    from termocast.config import Config
    cfg = Config(city="London")
    app = TermoCastApp(config=cfg)
    assert app.TITLE == "TermoCast"
