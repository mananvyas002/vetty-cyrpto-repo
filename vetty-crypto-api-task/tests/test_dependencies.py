import pytest
from fastapi import HTTPException

from app.dependencies import require_api_key
from config import settings


def test_valid_key_passes():
    require_api_key(settings.api_key)


def test_missing_key_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(None)
    assert exc_info.value.status_code == 401


def test_wrong_key_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        require_api_key("wrong-key")
    assert exc_info.value.status_code == 401
