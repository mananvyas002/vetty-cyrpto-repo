import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import require_api_key
from app.exceptions import ExternalServiceError, ExternalServiceTimeout
from app.logging_config import configure_logging
from app.models.models import (
    Category,
    Coin,
    HealthResponse,
    MarketItem,
    PaginatedResponse,
)
from app.services.crypto_services import CryptoService
from app.utils.cache import TTLCache
from app.utils.coingecko import CoinGeckoClient
from config import settings

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


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


@app.exception_handler(ExternalServiceTimeout)
async def external_timeout_handler(
    _: Request, exc: ExternalServiceTimeout
) -> JSONResponse:
    logger.warning("external_service_timeout")
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "error": {
                "code": "EXTERNAL_TIMEOUT",
                "message": "Cryptocurrency service timed out",
            }
        },
    )


@app.exception_handler(ExternalServiceError)
async def external_error_handler(_: Request, exc: ExternalServiceError) -> JSONResponse:
    logger.error("external_service_failure")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": {
                "code": "EXTERNAL_SERVICE_ERROR",
                "message": "Cryptocurrency service unavailable",
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", extra={"error": str(exc)})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
            }
        },
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


@app.get(
    "/categories",
    response_model=PaginatedResponse,
    dependencies=[Depends(require_api_key)],
    tags=["Categories"],
)
async def list_categories(
    request: Request,
    page_num: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
) -> PaginatedResponse:
    items = [
        Category(id=x["category_id"], name=x["name"])
        for x in await request.app.state.crypto.categories()
    ]
    return paginate(items, page_num, per_page)


@app.get(
    "/markets",
    response_model=PaginatedResponse,
    dependencies=[Depends(require_api_key)],
    tags=["Market Data"],
)
async def market_data(
    request: Request,
    coin_id: str | None = Query(default=None, min_length=1),
    category: str | None = Query(default=None, min_length=1),
    page_num: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
) -> PaginatedResponse:
    if not coin_id and not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "coin_id or category is required",
            },
        )
    raw_items = await request.app.state.crypto.markets(coin_id, category)
    items = [MarketItem.model_validate(x) for x in raw_items]
    return paginate(items, page_num, per_page)
