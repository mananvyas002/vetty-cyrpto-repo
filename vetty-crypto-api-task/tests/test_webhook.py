import httpx

from app.utils.webhook import notify_webhook


class FakeResponse:
    def raise_for_status(self):
        pass


async def test_no_op_when_url_is_none(monkeypatch):
    called = False

    async def fake_post(self, url, json=None):
        nonlocal called
        called = True
        return FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    await notify_webhook(None, {"a": 1}, 3.0)
    assert called is False


async def test_posts_payload_when_url_set(monkeypatch):
    captured = {}

    async def fake_post(self, url, json=None):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    await notify_webhook("https://webhook.example.com", {"event": "x"}, 3.0)

    assert captured["url"] == "https://webhook.example.com"
    assert captured["json"] == {"event": "x"}


async def test_swallows_http_errors(monkeypatch):
    async def fake_post(self, url, json=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    await notify_webhook("https://webhook.example.com", {"event": "x"}, 3.0)
