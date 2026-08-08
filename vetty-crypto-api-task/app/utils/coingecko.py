import logging
from typing import Any

import httpx

from app.exceptions import ExternalServiceError, ExternalServiceTimeout

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    def __init__(self, base_url: str, api_key: str | None, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"accept": "application/json"}
        if api_key:
            self.headers["x-cg-demo-api-key"] = api_key

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{path}", headers=self.headers, params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            logger.warning("external_api_timeout", extra={"path": path})
            raise ExternalServiceTimeout from exc
        except httpx.HTTPError as exc:
            logger.error(
                "external_api_error",
                extra={"path": path, "error": str(exc)},
            )
            raise ExternalServiceError from exc

    async def ping(self) -> dict[str, Any]:
        return await self._get("/ping")

    async def coins_list(self) -> list[dict[str, Any]]:
        return await self._get("/coins/list")

    async def categories_list(self) -> list[dict[str, Any]]:
        return await self._get("/coins/categories/list")

    async def markets(
        self, coin_id: str | None, category: str | None
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "vs_currency": "cad",
            "order": "market_cap_desc",
            "sparkline": "false",
        }
        if coin_id:
            params["ids"] = coin_id
        if category:
            params["category"] = category
        return await self._get("/coins/markets", params=params)
