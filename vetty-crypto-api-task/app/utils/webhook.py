import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def notify_webhook(
    webhook_url: str | None, payload: dict[str, Any], timeout: float
) -> None:
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            await client.post(webhook_url, json=payload)
    except httpx.HTTPError as exc:
        logger.warning("webhook_notify_failed", extra={"error": str(exc)})
