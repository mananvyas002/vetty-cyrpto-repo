import httpx
import pytest

from app.exceptions import ExternalServiceError, ExternalServiceTimeout
from app.utils.coingecko import CoinGeckoClient


class FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def test_api_key_sets_header():
    client = CoinGeckoClient("https://api.example.com", "secret", 5.0)
    assert client.headers["x-cg-demo-api-key"] == "secret"


def test_no_api_key_omits_header():
    client = CoinGeckoClient("https://api.example.com", None, 5.0)
    assert "x-cg-demo-api-key" not in client.headers


async def test_ping_returns_json(monkeypatch):
    async def fake_get(self, url, headers=None, params=None):
        return FakeResponse({"gecko_says": "ok"})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    client = CoinGeckoClient("https://api.example.com", None, 5.0)
    result = await client.ping()
    assert result == {"gecko_says": "ok"}


async def test_timeout_raises_external_service_timeout(monkeypatch):
    async def fake_get(self, url, headers=None, params=None):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    client = CoinGeckoClient("https://api.example.com", None, 5.0)
    with pytest.raises(ExternalServiceTimeout):
        await client.ping()


async def test_http_error_raises_external_service_error(monkeypatch):
    async def fake_get(self, url, headers=None, params=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    client = CoinGeckoClient("https://api.example.com", None, 5.0)
    with pytest.raises(ExternalServiceError):
        await client.ping()


async def test_markets_builds_params_for_coin_and_category(monkeypatch):
    captured = {}

    async def fake_get(self, url, headers=None, params=None):
        captured["params"] = params
        return FakeResponse([])

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    client = CoinGeckoClient("https://api.example.com", None, 5.0)
    await client.markets("bitcoin", "defi")

    assert captured["params"]["vs_currency"] == "cad"
    assert captured["params"]["ids"] == "bitcoin"
    assert captured["params"]["category"] == "defi"


async def test_markets_omits_unset_filters(monkeypatch):
    captured = {}

    async def fake_get(self, url, headers=None, params=None):
        captured["params"] = params
        return FakeResponse([])

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    client = CoinGeckoClient("https://api.example.com", None, 5.0)
    await client.markets("bitcoin", None)

    assert "ids" in captured["params"]
    assert "category" not in captured["params"]
