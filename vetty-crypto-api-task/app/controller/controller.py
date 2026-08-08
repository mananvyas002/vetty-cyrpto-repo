from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Query, Request
from config import settings
from app.dependencies import require_api_key
from app.models.models import Coin, HealthResponse, PaginatedResponse
from app.services.crypto_services import CryptoService
from app.utils.coingecko import CoinGeckoClient
from app.utils.cache import TTLCache


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = CoinGeckoClient(
        settings.coingecko_base_url,
        settings.coingecko_api_key,
        settings.coingecko_timeout_seconds,
    )
    app.state.crypto = CryptoService(
        client,
        TTLCache(settings.cache_ttl_seconds),
        settings.webhook_url,
        settings.webhook_timeout_seconds,
    )
    yield


app = FastAPI(
    title="Vetty Crypto Market API",
    version=settings.app_version,
    description=(
        "Async cryptocurrency market API built for the Vetty Python API exercise."
    ),
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health(request: Request) -> HealthResponse:
    external_status, external_version = await request.app.state.crypto.health()
    return HealthResponse(
        status="healthy" if external_status == "reachable" else "degraded",
        application_version=settings.app_version,
        cryptocurrency_service=external_status,
        cryptocurrency_service_version=external_version,
    )


def paginate(items: list, page_num: int, per_page: int) -> PaginatedResponse:
    start = (page_num - 1) * per_page
    return PaginatedResponse(
        page_num=page_num,
        per_page=per_page,
        total=len(items),
        data=items[start : start + per_page],
    )


@app.get(
    "/coins",
    response_model=PaginatedResponse,
    dependencies=[Depends(require_api_key)],
    tags=["Coins"],
)
async def list_coins(
    request: Request,
    page_num: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
) -> PaginatedResponse:
    items = [
        Coin(id=x["id"], name=x["name"], symbol=x["symbol"])
        for x in await request.app.state.crypto.coins()
    ]
    return paginate(items, page_num, per_page)
