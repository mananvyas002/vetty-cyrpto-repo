import time

from app.utils.cache import TTLCache


def test_set_and_get_returns_value():
    cache = TTLCache(ttl_seconds=60)
    cache.set("key", {"a": 1})
    assert cache.get("key") == {"a": 1}


def test_get_missing_key_returns_none():
    cache = TTLCache(ttl_seconds=60)
    assert cache.get("missing") is None


def test_entry_expires_after_ttl(monkeypatch):
    cache = TTLCache(ttl_seconds=1)
    cache.set("key", "value")

    real_monotonic = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: real_monotonic + 2)

    assert cache.get("key") is None


def test_clear_removes_all_entries():
    cache = TTLCache(ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
