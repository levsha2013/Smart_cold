"""ORM-модели SQLAlchemy 2.x."""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Unit(str, enum.Enum):
    pcs = "шт"
    g = "г"
    kg = "кг"
    ml = "мл"
    l = "л"


class Action(str, enum.Enum):
    added = "added"
    consumed = "consumed"
    removed = "removed"
    expired = "expired"
    opened = "opened"


class ShelfLifeBasis(str, enum.Enum):
    production = "production"  # срок считается от даты изготовления
    purchase = "purchase"     # срок считается от даты покупки/добавления


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class StorageLocation(Base):
    __tablename__ = "storage_locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    products: Mapped[list["Product"]] = relationship(back_populates="location")


class ShelfLifeDefault(Base):
    """Словарь типовых сроков годности для подстановки при добавлении продукта."""
    __tablename__ = "shelf_life_defaults"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_pattern: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    basis: Mapped[ShelfLifeBasis] = mapped_column(
        Enum(ShelfLifeBasis), default=ShelfLifeBasis.production, nullable=False
    )
    days_after_opening: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("storage_locations.id"), nullable=True)

    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    unit: Mapped[Unit] = mapped_column(Enum(Unit), default=Unit.pcs, nullable=False)

    production_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    opened_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    added_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)

    category: Mapped[Category | None] = relationship(back_populates="products")
    location: Mapped[StorageLocation | None] = relationship(back_populates="products")
    # Без каскадного удаления: при удалении продукта история сохраняется,
    # а product_id обнуляется (ondelete SET NULL). product_name хранит имя на момент события.
    events: Mapped[list["HistoryEvent"]] = relationship(back_populates="product")


class HistoryEvent(Base):
    __tablename__ = "history_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[Action] = mapped_column(Enum(Action), nullable=False)
    quantity_delta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    product: Mapped[Product | None] = relationship(back_populates="events")


class ShoppingItem(Base):
    __tablename__ = "shopping_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[Unit | None] = mapped_column(Enum(Unit), nullable=True)
    done: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Recipe(Base):
    """Под будущую генерацию рецептов (LLM). В MVP не заполняется."""
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    ingredients: Mapped[str] = mapped_column(Text, default="[]", nullable=False)  # JSON
    instructions: Mapped[str] = mapped_column(Text, default="", nullable=False)
