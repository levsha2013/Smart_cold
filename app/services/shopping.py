"""Логика списка покупок: автодобавление при списании продукта в 0."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, ShoppingItem


def add_from_product(db: Session, product: Product) -> ShoppingItem | None:
    """Добавить продукт в список покупок при списании в 0 (без дублей среди невыполненных)."""
    existing = db.scalar(
        select(ShoppingItem).where(
            ShoppingItem.name == product.name, ShoppingItem.done.is_(False)
        )
    )
    if existing is not None:
        return existing
    item = ShoppingItem(name=product.name, unit=product.unit)
    db.add(item)
    db.flush()
    return item
