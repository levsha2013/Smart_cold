"""Операции над БД: продукты, история, список покупок, справочники."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Action,
    Category,
    HistoryEvent,
    Product,
    ShoppingItem,
    StorageLocation,
)
from app.schemas import ProductCreate


# --- Справочники ---

def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def list_locations(db: Session) -> list[StorageLocation]:
    return list(db.scalars(select(StorageLocation).order_by(StorageLocation.name)))


# --- Продукты ---

def list_products(db: Session) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.expiry_date.is_(None), Product.expiry_date)))


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def _log(db: Session, product: Product, action: Action, delta: float = 0.0) -> None:
    db.add(
        HistoryEvent(
            product_id=product.id,
            product_name=product.name,
            action=action,
            quantity_delta=delta,
        )
    )


def add_product(db: Session, data: ProductCreate) -> Product:
    product = Product(
        name=data.name,
        category_id=data.category_id,
        location_id=data.location_id,
        quantity=data.quantity,
        unit=data.unit,
        production_date=data.production_date,
        expiry_date=data.expiry_date,
        notes=data.notes,
        source=data.source,
        added_date=date.today(),
    )
    db.add(product)
    db.flush()  # получаем product.id
    _log(db, product, Action.added, data.quantity)
    db.commit()
    db.refresh(product)
    return product


def set_quantity(db: Session, product: Product, quantity: float) -> Product:
    delta = quantity - product.quantity
    product.quantity = max(quantity, 0.0)
    _log(db, product, Action.consumed if delta < 0 else Action.added, delta)
    db.commit()
    db.refresh(product)
    return product


def consume(db: Session, product: Product, amount: float) -> Product:
    """Списать amount единиц. При обнулении продукт удаляется и попадает в список покупок."""
    amount = min(amount, product.quantity)
    product.quantity -= amount
    _log(db, product, Action.consumed, -amount)
    if product.quantity <= 0:
        from app.services.shopping import add_from_product

        add_from_product(db, product)
        db.delete(product)
        db.commit()
        return product
    db.commit()
    db.refresh(product)
    return product


def mark_opened(db: Session, product: Product) -> Product:
    product.opened_date = date.today()
    _log(db, product, Action.opened)
    db.commit()
    db.refresh(product)
    return product


def remove_product(db: Session, product: Product) -> None:
    _log(db, product, Action.removed, -product.quantity)
    db.delete(product)
    db.commit()


# --- История ---

def list_history(db: Session, limit: int = 200) -> list[HistoryEvent]:
    return list(
        db.scalars(select(HistoryEvent).order_by(HistoryEvent.created_at.desc()).limit(limit))
    )


# --- Список покупок ---

def list_shopping(db: Session) -> list[ShoppingItem]:
    return list(
        db.scalars(select(ShoppingItem).order_by(ShoppingItem.done, ShoppingItem.created_at.desc()))
    )


def add_shopping_item(db: Session, name: str, quantity: float | None = None, unit=None) -> ShoppingItem:
    item = ShoppingItem(name=name, quantity=quantity, unit=unit)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def toggle_shopping_item(db: Session, item_id: int) -> ShoppingItem | None:
    item = db.get(ShoppingItem, item_id)
    if item is None:
        return None
    item.done = not item.done
    db.commit()
    db.refresh(item)
    return item


def delete_shopping_item(db: Session, item_id: int) -> None:
    item = db.get(ShoppingItem, item_id)
    if item is not None:
        db.delete(item)
        db.commit()
