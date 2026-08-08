from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    application_version: str
    cryptocurrency_service: str
    cryptocurrency_service_version: str | None = None
