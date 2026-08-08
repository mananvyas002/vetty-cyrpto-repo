from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    application_version: str
    cryptocurrency_service: str
    cryptocurrency_service_version: str | None = None


class Coin(BaseModel):
    id: str
    name: str
    symbol: str


class Category(BaseModel):
    id: str
    name: str


class MarketItem(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: float | None = None
    market_cap: float | None = None
    market_cap_rank: int | None = None
    price_change_percentage_24h: float | None = None


class PaginatedResponse(BaseModel):
    page_num: int = Field(ge=1)
    per_page: int = Field(ge=1)
    total: int
    data: list[Any]
