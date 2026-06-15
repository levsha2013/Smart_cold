"""Тесты вычисления статуса свежести и подстановки срока из словаря."""
from __future__ import annotations

from datetime import date, timedelta

from app.models import Category, Product, Unit
from app.services import freshness


def _product(expiry=None, **kw):
    return Product(name=kw.pop("name", "Тест"), quantity=1, unit=Unit.pcs, expiry_date=expiry, **kw)


def test_fresh_when_far_from_expiry():
    p = _product(expiry=date.today() + timedelta(days=30))
    assert freshness.assess(p).status == freshness.FRESH


def test_expiring_within_warn_days():
    p = _product(expiry=date.today() + timedelta(days=2))
    f = freshness.assess(p)
    assert f.status == freshness.EXPIRING
    assert f.days_left == 2


def test_expired_in_past():
    p = _product(expiry=date.today() - timedelta(days=1))
    f = freshness.assess(p)
    assert f.status == freshness.EXPIRED
    assert f.days_left == -1


def test_unknown_without_expiry():
    p = _product(expiry=None)
    assert freshness.assess(p).status == freshness.UNKNOWN


def test_suggest_expiry_from_dictionary(db):
    # молоко: 7 дней от даты изготовления
    prod = date(2026, 6, 1)
    suggested = freshness.suggest_expiry(db, "молоко домашнее", "Молочное", prod, date.today())
    assert suggested == prod + timedelta(days=7)


def test_suggest_expiry_eggs(db):
    prod = date(2026, 6, 1)
    suggested = freshness.suggest_expiry(db, "яйца куриные", "Прочее", prod, date.today())
    assert suggested == prod + timedelta(days=30)


def test_suggest_expiry_none_for_unknown(db):
    assert freshness.suggest_expiry(db, "неведомый товар", None, date.today(), date.today()) is None


def test_opened_shortens_expiry(db):
    cat = db.query(Category).filter_by(name="Молочное").one()
    # срок далеко, но вскрыто сегодня → молоко +3 дня после вскрытия
    p = _product(
        name="молоко", expiry=date.today() + timedelta(days=30),
        opened_date=date.today(), category=cat,
    )
    eff = freshness.effective_expiry(p)
    assert eff == date.today() + timedelta(days=3)
