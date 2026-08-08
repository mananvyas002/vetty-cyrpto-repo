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


class PaginatedResponse(BaseModel):
    page_num: int = Field(ge=1)
    per_page: int = Field(ge=1)
    total: int
    data: list[Any]
