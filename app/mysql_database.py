"""MySQL CRUD adapter matching the existing SQLite module's public functions.

The Path argument is retained so the FastAPI routes and SQLite test fixtures
can use either backend without changing their function calls.
"""

import os
from pathlib import Path

from app.schemas import Car, CarInput


def connect():
    # Import only when the MySQL backend is selected. SQLite-only tests stay isolated.
    import pymysql
    from pymysql.constants import CLIENT
    from pymysql.cursors import DictCursor

    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "db"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        client_flag=CLIENT.FOUND_ROWS,
        connect_timeout=10,
    )


def initialize(_database_path: Path) -> None:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cars (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                make VARCHAR(60) NOT NULL,
                model VARCHAR(60) NOT NULL,
                year INT NOT NULL,
                color VARCHAR(40) NOT NULL DEFAULT '',
                CONSTRAINT valid_make CHECK (CHAR_LENGTH(TRIM(make)) > 0),
                CONSTRAINT valid_model CHECK (CHAR_LENGTH(TRIM(model)) > 0),
                CONSTRAINT valid_year CHECK (year BETWEEN 1886 AND 2100)
            ) CHARACTER SET utf8mb4
            """
        )


def list_cars(_database_path: Path) -> list[Car]:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, make, model, year, color FROM cars ORDER BY id DESC")
        return [Car(**row) for row in cursor.fetchall()]


def get_car(_database_path: Path, car_id: int) -> Car | None:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, make, model, year, color FROM cars WHERE id = %s",
            (car_id,)
        )
        row = cursor.fetchone()
        return Car(**row) if row else None


def create_car(_database_path: Path, car: CarInput) -> Car:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO cars (make, model, year, color) VALUES (%s, %s, %s, %s)",
            (car.make, car.model, car.year, car.color),
        )
        return Car(id=cursor.lastrowid, **car.model_dump())


def update_car(_database_path: Path, car_id: int, car: CarInput) -> Car | None:
    with connect() as connection, connection.cursor() as cursor:
        matched = cursor.execute(
            "UPDATE cars SET make = %s, model = %s, year = %s, color = %s WHERE id = %s",
            (car.make, car.model, car.year, car.color, car_id),
        )
        return Car(id=car_id, **car.model_dump()) if matched else None


def delete_car(_database_path: Path, car_id: int) -> bool:
    with connect() as connection, connection.cursor() as cursor:
        deleted = cursor.execute("DELETE FROM cars WHERE id = %s", (car_id,))
        return deleted == 1
