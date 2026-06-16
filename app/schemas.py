"""Pydantic-схемы для валидации ввода и обмена данными между слоями."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.models import Unit


class ParsedProduct(BaseModel):
    """Единый формат продукта от любого источника ввода (форма, фото, голос)."""
    name: str
    quantity: float = 1.0
    unit: Unit = Unit.pcs
    category: str | None = None
    production_date: date | None = None
    expiry_date: date | None = None
    days_after_opening: int | None = None
    notes: str | None = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: float = Field(default=1.0, ge=0)
    unit: Unit = Unit.pcs
    category_id: int | None = None
    location_id: int | None = None
    production_date: date | None = None
    expiry_date: date | None = None
    days_after_opening: int | None = None
    notes: str | None = None
    source: str = "manual"


class ShoppingItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: float | None = None
    unit: Unit | None = None
