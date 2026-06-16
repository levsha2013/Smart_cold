"""Роутер продуктов: доска, добавление, редактирование, списание, вскрытие, удаление."""
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

NO_CATEGORY = "Без категории"


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    products = crud.list_products(db)

    # Группировка по категориям (порядок справочника), пустые группы не показываем.
    order = [c.name for c in crud.list_categories(db)] + [NO_CATEGORY]
    buckets: dict[str, list] = {name: [] for name in order}
    counts = {freshness.EXPIRED: 0, freshness.EXPIRING: 0, freshness.FRESH: 0, freshness.UNKNOWN: 0}
    for p in products:
        cat = p.category.name if p.category else NO_CATEGORY
        buckets.setdefault(cat, []).append(p)
        counts[freshness.assess(p).status] += 1

    groups = [{"name": name, "products": items} for name in order if (items := buckets.get(name))]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "groups": groups,
            "counts": counts,
            "total": len(products),
            "freshness": freshness,
        },
    )


@router.get("/products/new")
def new_product(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("product_form.html", _form_ctx(request, db, product=None))


@router.get("/products/{product_id}/edit")
def edit_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if product is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("product_form.html", _form_ctx(request, db, product=product))


@router.post("/products")
async def create_product(request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form())
    crud.add_product(db, _build_product(form))
    return RedirectResponse("/", status_code=303)


@router.post("/products/{product_id}/edit")
async def update_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form())
    product = crud.get_product(db, product_id)
    if product is not None:
        crud.update_product(db, product, _build_product(form))
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


# --- helpers ---

def _form_ctx(request: Request, db: Session, product) -> dict:
    return {
        "request": request,
        "product": product,
        "categories": crud.list_categories(db),
        "locations": crud.list_locations(db),
        "units": list(Unit),
        "today": date.today().isoformat(),
    }


def _build_product(form: dict) -> ProductCreate:
    """Собирает ProductCreate из полей формы (общий код для create и update)."""
    return ProductCreate(
        name=(form.get("name") or "").strip(),
        quantity=_to_float(form.get("quantity"), 1.0),
        unit=Unit(form.get("unit") or Unit.pcs.value),
        category_id=_to_int(form.get("category_id")),
        location_id=_to_int(form.get("location_id")),
        production_date=_parse_date(form.get("production_date")),
        expiry_date=_parse_date(form.get("expiry_date")),
        days_after_opening=_to_int(form.get("days_after_opening")),
        notes=(form.get("notes") or "").strip() or None,
    )


def _to_float(value, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return default


def _to_int(value) -> int | None:
    value = (str(value) if value is not None else "").strip()
    if not value:
        return None
    try:
        return int(float(value.replace(",", ".")))
    except (ValueError, TypeError):
        return None


def _parse_date(value) -> date | None:
    value = (str(value) if value is not None else "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
