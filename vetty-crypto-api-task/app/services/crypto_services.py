import logging
from typing import Any

from app.utils.cache import TTLCache
from app.utils.coingecko import CoinGeckoClient
from app.utils.webhook import notify_webhook

logger = logging.getLogger(__name__)



class CryptoService:
    def __init__(
        self,
        client: CoinGeckoClient,
        cache: TTLCache,
        webhook_url: str | None,
        webhook_timeout: float,
    ) -> None:
        self.client = client
        self.cache = cache
        self.webhook_url = webhook_url
        self.webhook_timeout = webhook_timeout

    async def _cached(
        self, key: str, loader: Any, notify_payload: dict | None = None
    ) -> Any:
        cached = self.cache.get(key)
        if cached is not None:
            logger.info("cache_hit", extra={"cache_key": key})
            return cached
        value = await loader()
        self.cache.set(key, value)
        if notify_payload is not None:
            await notify_webhook(
                self.webhook_url, notify_payload, self.webhook_timeout
            )
        return value

    async def health(self) -> tuple[str, str | None]:
        try:
            result = await self.client.ping()
            # CoinGecko's public API exposes no stable API version in /ping.
            return "reachable", result.get("version")
        except Exception:
            return "unreachable", None

    async def coins(self) -> list[dict[str, Any]]:
        return await self._cached(
            "coins:list",
            self.client.coins_list,
            None,
        )

