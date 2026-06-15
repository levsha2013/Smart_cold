"""Роутер продуктов: список, добавление, списание, вскрытие, удаление + API подсказки срока."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import Unit
from app.schemas import ProductCreate
from app.services import freshness
from app.templating import templates

router = APIRouter()


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    products = crud.list_products(db)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": products, "freshness": freshness},
    )


@router.get("/products/new")
def new_product(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "product_form.html",
        {
            "request": request,
            "categories": crud.list_categories(db),
            "locations": crud.list_locations(db),
            "units": list(Unit),
            "today": date.today().isoformat(),
        },
    )


@router.post("/products")
def create_product(
    db: Session = Depends(get_db),
    name: str = Form(...),
    quantity: float = Form(1.0),
    unit: str = Form(Unit.pcs.value),
    category_id: str = Form(""),
    location_id: str = Form(""),
    production_date: str = Form(""),
    expiry_date: str = Form(""),
    notes: str = Form(""),
):
    data = ProductCreate(
        name=name.strip(),
        quantity=quantity,
        unit=Unit(unit),
        category_id=int(category_id) if category_id else None,
        location_id=int(location_id) if location_id else None,
        production_date=_parse_date(production_date),
        expiry_date=_parse_date(expiry_date),
        notes=notes.strip() or None,
    )
    crud.add_product(db, data)
    return RedirectResponse("/", status_code=303)


@router.post("/products/{product_id}/consume")
def consume_product(product_id: int, amount: float = Form(...), db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if product is not None:
        crud.consume(db, product, amount)
    return RedirectResponse("/", status_code=303)


@router.post("/products/{product_id}/open")
def open_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if product is not None:
        crud.mark_opened(db, product)
    return RedirectResponse("/", status_code=303)


@router.post("/products/{product_id}/delete")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if product is not None:
        crud.remove_product(db, product)
    return RedirectResponse("/", status_code=303)


@router.get("/api/suggest-expiry")
def suggest_expiry(
    name: str,
    category: str | None = None,
    production_date: str | None = None,
    db: Session = Depends(get_db),
):
    """JSON-подсказка срока годности из словаря (для автоподстановки в форме)."""
    suggested = freshness.suggest_expiry(
        db, name, category, _parse_date(production_date or ""), date.today()
    )
    return {"expiry_date": suggested.isoformat() if suggested else None}


def _parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
