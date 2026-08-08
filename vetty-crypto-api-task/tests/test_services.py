from app.services.crypto_services import CryptoService
from app.utils.cache import TTLCache


class FakeClient:
    def __init__(self):
        self.coins_calls = 0

    async def ping(self):
        return {"version": "1.2.3"}

    async def coins_list(self):
        self.coins_calls += 1
        return [{"id": "bitcoin"}]


class FailingPingClient:
    async def ping(self):
        raise RuntimeError("down")


class MarketClient:
    async def markets(self, coin_id, category):
        return [{"id": "bitcoin"}]


async def test_health_returns_reachable_with_version():
    service = CryptoService(FakeClient(), TTLCache(60), None, 3.0)
    status_, version = await service.health()
    assert status_ == "reachable"
    assert version == "1.2.3"


async def test_health_returns_unreachable_on_error():
    service = CryptoService(FailingPingClient(), TTLCache(60), None, 3.0)
    status_, version = await service.health()
    assert status_ == "unreachable"
    assert version is None


async def test_coins_uses_cache_on_second_call():
    client = FakeClient()
    service = CryptoService(client, TTLCache(60), None, 3.0)

    first = await service.coins()
    second = await service.coins()

    assert first == second == [{"id": "bitcoin"}]
    assert client.coins_calls == 1


async def test_markets_notifies_webhook_only_on_cache_miss(monkeypatch):
    calls = []

    async def fake_notify(url, payload, timeout):
        calls.append(payload)

    monkeypatch.setattr("app.services.crypto_services.notify_webhook", fake_notify)

    service = CryptoService(MarketClient(), TTLCache(60), "https://hook", 3.0)
    await service.markets("bitcoin", None)
    await service.markets("bitcoin", None)

    assert len(calls) == 1
    assert calls[0]["coin_id"] == "bitcoin"
    assert calls[0]["event"] == "market_data_retrieved"
