import pytest
from fastapi.testclient import TestClient

from app.controller.controller import app
from config import settings


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_key_headers():
    return {"X-API-Key": settings.api_key}
