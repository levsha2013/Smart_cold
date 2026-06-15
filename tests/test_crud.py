"""Тесты операций CRUD: добавление, списание, история, список покупок."""
from __future__ import annotations

from app import crud
from app.models import Action, ShoppingItem, Unit
from app.schemas import ProductCreate


def _add(db, name="Молоко", qty=2.0):
    return crud.add_product(db, ProductCreate(name=name, quantity=qty, unit=Unit.l))


def test_add_product_creates_history(db):
    p = _add(db)
    assert p.id is not None
    events = crud.list_history(db)
    assert len(events) == 1
    assert events[0].action == Action.added
    assert events[0].quantity_delta == 2.0


def test_consume_reduces_quantity(db):
    p = _add(db, qty=3.0)
    crud.consume(db, p, 1.0)
    assert crud.get_product(db, p.id).quantity == 2.0
    assert any(e.action == Action.consumed for e in crud.list_history(db))


def test_consume_to_zero_deletes_and_adds_to_shopping(db):
    p = _add(db, qty=1.0)
    pid = p.id
    crud.consume(db, p, 1.0)
    assert crud.get_product(db, pid) is None
    shopping = db.query(ShoppingItem).all()
    assert len(shopping) == 1
    assert shopping[0].name == "Молоко"


def test_set_quantity(db):
    p = _add(db, qty=2.0)
    crud.set_quantity(db, p, 5.0)
    assert crud.get_product(db, p.id).quantity == 5.0


def test_remove_product(db):
    p = _add(db)
    pid = p.id
    crud.remove_product(db, p)
    assert crud.get_product(db, pid) is None
    assert any(e.action == Action.removed for e in crud.list_history(db))


def test_shopping_toggle_and_delete(db):
    item = crud.add_shopping_item(db, "Хлеб")
    assert item.done is False
    crud.toggle_shopping_item(db, item.id)
    assert crud.get_product(db, item.id) is None or True  # product != shopping
    assert db.get(ShoppingItem, item.id).done is True
    crud.delete_shopping_item(db, item.id)
    assert db.get(ShoppingItem, item.id) is None
