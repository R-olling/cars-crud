"""Tier 1: isolated validation, without a server or database."""

import pytest
from pydantic import ValidationError

from app.schemas import CarInput

pytestmark = pytest.mark.unit


def test_strips_surrounding_whitespace():
    car = CarInput(make=" Toyota ", model=" Corolla ", year=2024, color=" Silver ")
    assert car.model_dump() == {
        "make": "Toyota", "model": "Corolla", "year": 2024, "color": "Silver"
    }


def test_color_is_optional():
    car = CarInput(make="Toyota", model="Corolla", year=2024)
    assert car.color == "Blue"


@pytest.mark.parametrize("year", [1886, 2100])
def test_year_boundaries_are_allowed(year):
    assert CarInput(make="Toyota", model="Corolla", year=year).year == year


@pytest.mark.parametrize(
    "field,value",
    [
        ("make", ""), ("make", "   "), ("make", "x" * 61), ("make", None),
        ("model", ""), ("model", "\t"), ("model", "x" * 61),
        ("year", 1885), ("year", 2101), ("year", 2024.5),
        ("year", True), ("year", "2024"),
        ("color", "x" * 41), ("color", None),
    ],
)
def test_invalid_fields_are_rejected(car_payload, field, value):
    car_payload[field] = value
    with pytest.raises(ValidationError):
        CarInput(**car_payload)


@pytest.mark.parametrize("field", ["make", "model", "year"])
def test_required_fields_cannot_be_omitted(car_payload, field):
    del car_payload[field]
    with pytest.raises(ValidationError):
        CarInput(**car_payload)


def test_unknown_fields_are_rejected(car_payload):
    with pytest.raises(ValidationError):
        CarInput(**car_payload, price=10000)
