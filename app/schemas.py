"""Request/response models and validation rules; no database access here."""

from pydantic import BaseModel, ConfigDict, Field


class CarInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    make: str = Field(min_length=1, max_length=60)
    model: str = Field(min_length=1, max_length=60)
    year: int = Field(strict=True, ge=1886, le=2100)
    color: str = Field(default="", max_length=40)


class Car(CarInput):
    id: int = Field(gt=0)
