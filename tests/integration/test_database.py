"""Tier 2: Python code integrated with a real temporary SQLite file."""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import create_app
from app.schemas import CarInput

pytestmark = pytest.mark.integration


@pytest.fixture
def db(database_path: Path) -> Path:
    database.initialize(database_path)
    return database_path


def test_crud_against_sqlite(db, car_payload):
    assert database.list_cars(db) == []
    car = database.create_car(db, CarInput(**car_payload))
    assert car.id > 0
    assert database.get_car(db, car.id) == car

    updated = database.update_car(db, car.id, CarInput(make="Honda", model="Civic", year=2025))
    assert updated.id == car.id
    assert database.get_car(db, car.id).model == "Civic"
    assert database.get_car(db, car.id).color == ""

    assert database.delete_car(db, car.id) is True
    assert database.get_car(db, car.id) is None
    assert database.list_cars(db) == []


def test_newest_car_is_listed_first(db, car_payload):
    first = database.create_car(db, CarInput(**car_payload))
    second = database.create_car(db, CarInput(**car_payload))
    assert [car.id for car in database.list_cars(db)] == [second.id, first.id]


def test_missing_car_does_not_create_or_delete_anything(db, car_payload):
    assert database.get_car(db, 999) is None
    assert database.update_car(db, 999, CarInput(**car_payload)) is None
    assert database.delete_car(db, 999) is False
    assert database.list_cars(db) == []


def test_initialize_preserves_existing_rows(db, car_payload):
    car = database.create_car(db, CarInput(**car_payload))
    database.initialize(db)
    assert database.get_car(db, car.id) == car


def test_sql_characters_are_stored_as_data(db):
    suspicious_text = "'); DROP TABLE cars; --"
    car = database.create_car(db, CarInput(make=suspicious_text, model="Test", year=2024))
    assert database.get_car(db, car.id).make == suspicious_text
    assert len(database.list_cars(db)) == 1


def test_failed_transaction_rolls_back(db):
    with pytest.raises(RuntimeError):
        with database.connect(db) as connection:
            connection.execute(
                "INSERT INTO cars (make, model, year) VALUES (?, ?, ?)",
                ("Toyota", "Corolla", 2024),
            )
            raise RuntimeError("Simulated failure before commit")
    assert database.list_cars(db) == []


def test_database_rejects_invalid_year(db):
    with pytest.raises(sqlite3.IntegrityError):
        with database.connect(db) as connection:
            connection.execute(
                "INSERT INTO cars (make, model, year) VALUES (?, ?, ?)",
                ("Toyota", "Corolla", 1700),
            )
    assert database.list_cars(db) == []


def test_car_survives_application_restart(database_path, car_payload):
    with TestClient(create_app(database_path)) as first_app:
        created = first_app.post("/api/cars", json=car_payload).json()

    # A new app instance opens the SAME file, not an in-memory database.
    with TestClient(create_app(database_path)) as restarted_app:
        response = restarted_app.get(f"/api/cars/{created['id']}")
        assert response.status_code == 200
        assert response.json() == created
