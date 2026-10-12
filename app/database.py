"""SQLite CRUD using only the Python standard library. No ORM."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.schemas import Car, CarInput


@contextmanager
def connect(database_path: Path) -> Iterator[sqlite3.Connection]:
    # A fresh connection per operation keeps connections on their owning thread.
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        # Commit on success, roll back on failure.
        with connection:
            yield connection
    finally:
        # sqlite3's connection context manager does NOT close the connection.
        connection.close()


def initialize(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT NOT NULL CHECK(length(trim(make)) BETWEEN 1 AND 60),
                model TEXT NOT NULL CHECK(length(trim(model)) BETWEEN 1 AND 60),
                year INTEGER NOT NULL CHECK(year BETWEEN 1886 AND 2100),
                color TEXT NOT NULL DEFAULT '' CHECK(length(color) <= 40)
            )
            """
        )


def list_cars(database_path: Path) -> list[Car]:
    with connect(database_path) as connection:
        rows = connection.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
        return [Car(**dict(row)) for row in rows]


def get_car(database_path: Path, car_id: int) -> Car | None:
    with connect(database_path) as connection:
        row = connection.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
        return Car(**dict(row)) if row is not None else None


def create_car(database_path: Path, car: CarInput) -> Car:
    with connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO cars (make, model, year, color) VALUES (?, ?, ?, ?)",
            (car.make, car.model, car.year, car.color),
        )
        return Car(id=cursor.lastrowid, **car.model_dump())


def update_car(database_path: Path, car_id: int, car: CarInput) -> Car | None:
    with connect(database_path) as connection:
        cursor = connection.execute(
            "UPDATE cars SET make = ?, model = ?, year = ?, color = ? WHERE id = ?",
            (car.make, car.model, car.year, car.color, car_id),
        )
        if cursor.rowcount == 0:
            return None
        return Car(id=car_id, **car.model_dump())


def delete_car(database_path: Path, car_id: int) -> bool:
    with connect(database_path) as connection:
        cursor = connection.execute("DELETE FROM cars WHERE id = ?", (car_id,))
        return cursor.rowcount == 1
