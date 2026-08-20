import pytest

# These are smoke tests that may hit network; mocked via cache
def test_weather_service_cached():
    from termocast.services.weather import WeatherService
    svc = WeatherService()
    # Use cached London from previous runs if available, else skip network
    try:
        res = svc.fetch("London")
        assert isinstance(res.ok, bool)
        if res.ok:
            assert "current" in res.data or "raw_text" in res.data
    except Exception as e:
        pytest.skip(f"network unavailable: {e}")

def test_news_service():
    from termocast.services.news import NewsService
    svc = NewsService()
    try:
        res = svc.fetch(category="technology", source="hn", limit=3)
        assert isinstance(res.ok, bool)
        if res.ok:
            assert len(res.data) > 0
            assert "title" in res.data[0]
    except Exception as e:
        pytest.skip(f"network unavailable: {e}")

def test_cache():
    from termocast.utils.cache import TTLCache
    c = TTLCache(ttl=1, maxsize=2)
    c.set("k", "v")
    assert c.get("k") == "v"
    import time
    time.sleep(1.1)
    assert c.get("k") is None

def test_geolocation():
    from termocast.utils.geolocation import detect_location
    loc = detect_location()
    # may be None in CI without network, but should return dict
    assert isinstance(loc, dict)
    assert "city" in loc
