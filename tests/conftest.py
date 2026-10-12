from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "test-cars.db"


@pytest.fixture
def client(database_path: Path) -> Iterator[TestClient]:
    # The context manager runs FastAPI's lifespan, including table creation.
    # Each test gets a fresh on-disk database, never the real cars.db.
    with TestClient(create_app(database_path)) as test_client:
        yield test_client


@pytest.fixture
def car_payload() -> dict:
    return {"make": "Toyota", "model": "Corolla", "year": 2024, "color": "Silver"}
