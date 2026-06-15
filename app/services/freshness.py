"""Вычисление статуса свежести продукта и подстановка срока из словаря."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Product, ShelfLifeBasis, ShelfLifeDefault

FRESH = "fresh"
EXPIRING = "expiring"
EXPIRED = "expired"
UNKNOWN = "unknown"

STATUS_LABELS = {
    FRESH: "🟢 Свежий",
    EXPIRING: "🟡 Скоро истечёт",
    EXPIRED: "🔴 Истёк",
    UNKNOWN: "⚪ Срок не задан",
}


@dataclass
class Freshness:
    status: str
    effective_expiry: date | None
    days_left: int | None

    @property
    def label(self) -> str:
        return STATUS_LABELS[self.status]


def effective_expiry(product: Product) -> date | None:
    """Эффективный срок годности с учётом вскрытия.

    Если задан expiry_date — используем его (после вскрытия может сократиться).
    Если expiry_date нет — пробуем посчитать из словаря по production/added дате.
    """
    expiry = product.expiry_date
    if expiry is None:
        return None
    if product.opened_date and product.category:
        # после вскрытия срок может сократиться (days_after_opening из словаря)
        match = _lookup_default(product.name, product.category.name)
        if match and match.days_after_opening is not None:
            opened_limit = product.opened_date + timedelta(days=match.days_after_opening)
            expiry = min(expiry, opened_limit)
    return expiry


def assess(product: Product, today: date | None = None) -> Freshness:
    today = today or date.today()
    expiry = effective_expiry(product)
    if expiry is None:
        return Freshness(UNKNOWN, None, None)
    days_left = (expiry - today).days
    if days_left < 0:
        status = EXPIRED
    elif days_left <= settings.warn_days:
        status = EXPIRING
    else:
        status = FRESH
    return Freshness(status, expiry, days_left)


def suggest_expiry(
    db: Session, name: str, category_name: str | None, production: date | None, added: date | None
) -> date | None:
    """Предложить срок годности по словарю. Возвращает None, если совпадений нет."""
    match = _lookup_default(name, category_name, db=db)
    if match is None:
        return None
    base = production if match.basis == ShelfLifeBasis.production else (added or date.today())
    if base is None:
        return None
    return base + timedelta(days=match.days)


_DEFAULTS_CACHE: list[ShelfLifeDefault] | None = None


def _lookup_default(
    name: str, category_name: str | None, db: Session | None = None
) -> ShelfLifeDefault | None:
    """Ищет запись словаря: сначала по подстроке в имени, затем по категории."""
    defaults = _load_defaults(db)
    lname = name.lower()
    for d in defaults:
        if d.name_pattern.lower() in lname:
            return d
    if category_name:
        for d in defaults:
            if d.category and d.category.lower() == category_name.lower():
                return d
    return None


def _load_defaults(db: Session | None) -> list[ShelfLifeDefault]:
    global _DEFAULTS_CACHE
    if db is not None:
        _DEFAULTS_CACHE = list(db.scalars(select(ShelfLifeDefault)))
    if _DEFAULTS_CACHE is None:
        return []
    return _DEFAULTS_CACHE
