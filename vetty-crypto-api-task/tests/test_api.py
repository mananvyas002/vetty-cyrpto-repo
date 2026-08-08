from app.exceptions import ExternalServiceError, ExternalServiceTimeout
from app.utils.coingecko import CoinGeckoClient

FAKE_COINS = [
    {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
    {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
]

FAKE_CATEGORIES = [{"category_id": "defi", "name": "DeFi"}]

FAKE_MARKETS = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 90000.0,
        "market_cap": 1_000_000.0,
        "market_cap_rank": 1,
        "price_change_percentage_24h": 1.2,
    }
]


def test_health_reachable(client, monkeypatch):
    async def fake_get(self, path, params=None):
        return {"gecko_says": "(V3) To the Moon!"}

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["cryptocurrency_service"] == "reachable"


def test_health_degraded_when_external_unreachable(client, monkeypatch):
    async def fake_get(self, path, params=None):
        raise ExternalServiceError

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["cryptocurrency_service"] == "unreachable"


def test_coins_requires_api_key(client):
    resp = client.get("/coins")
    assert resp.status_code == 401


def test_coins_rejects_wrong_key(client):
    resp = client.get("/coins", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


def test_coins_success(client, monkeypatch, api_key_headers):
    async def fake_get(self, path, params=None):
        assert path == "/coins/list"
        return FAKE_COINS

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/coins", headers=api_key_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["data"][0] == {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc"}


def test_coins_pagination(client, monkeypatch, api_key_headers):
    async def fake_get(self, path, params=None):
        return FAKE_COINS

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/coins?per_page=1&page_num=2", headers=api_key_headers)
    body = resp.json()
    assert body["page_num"] == 2
    assert body["per_page"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == "ethereum"


def test_categories_success(client, monkeypatch, api_key_headers):
    async def fake_get(self, path, params=None):
        assert path == "/coins/categories/list"
        return FAKE_CATEGORIES

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/categories", headers=api_key_headers)
    assert resp.status_code == 200
    assert resp.json()["data"][0] == {"id": "defi", "name": "DeFi"}


def test_markets_requires_filter(client, api_key_headers):
    resp = client.get("/markets", headers=api_key_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_markets_with_coin_id_returns_cad_pricing(client, monkeypatch, api_key_headers):
    async def fake_get(self, path, params=None):
        assert params["vs_currency"] == "cad"
        assert params["ids"] == "bitcoin"
        return FAKE_MARKETS

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/markets?coin_id=bitcoin", headers=api_key_headers)
    assert resp.status_code == 200
    assert resp.json()["data"][0]["current_price"] == 90000.0


def test_markets_external_timeout_returns_504(client, monkeypatch, api_key_headers):
    async def fake_get(self, path, params=None):
        raise ExternalServiceTimeout

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/markets?coin_id=bitcoin", headers=api_key_headers)
    assert resp.status_code == 504
    assert resp.json()["error"]["code"] == "EXTERNAL_TIMEOUT"


def test_markets_external_error_returns_502(client, monkeypatch, api_key_headers):
    async def fake_get(self, path, params=None):
        raise ExternalServiceError

    monkeypatch.setattr(CoinGeckoClient, "_get", fake_get)
    resp = client.get("/markets?coin_id=bitcoin", headers=api_key_headers)
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "EXTERNAL_SERVICE_ERROR"


def test_markets_per_page_over_limit_is_rejected(client, api_key_headers):
    resp = client.get("/markets?coin_id=bitcoin&per_page=101", headers=api_key_headers)
    assert resp.status_code == 422
