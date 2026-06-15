"""Роутер ингестии: текст/фото/голос → распознанные продукты → подтверждение → добавление."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import Unit
from app.schemas import ProductCreate
from app.services.ingestion import factory
from app.templating import templates

router = APIRouter()


@router.get("/ingest")
def ingest_form(request: Request):
    return templates.TemplateResponse("ingest.html", {"request": request})


@router.post("/ingest/text")
def ingest_text(request: Request, text: str = Form(...), db: Session = Depends(get_db)):
    result = factory.parse_text(text)
    return _review(request, result, db)


@router.post("/ingest/photo")
async def ingest_photo(request: Request, photo: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await photo.read()
    result = factory.parse_image(content, photo.content_type or "image/jpeg")
    return _review(request, result, db)


@router.post("/ingest/voice")
async def ingest_voice(request: Request, audio: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await audio.read()
    result = factory.transcribe(content, audio.filename or "voice.ogg")
    return _review(request, result, db)


@router.post("/ingest/confirm")
async def ingest_confirm(request: Request, db: Session = Depends(get_db)):
    """Принимает отредактированные строки из формы подтверждения и сохраняет продукты."""
    form = await request.form()
    names = form.getlist("name")
    quantities = form.getlist("quantity")
    units = form.getlist("unit")
    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            continue
        crud.add_product(
            db,
            ProductCreate(
                name=name,
                quantity=_to_float(quantities[i] if i < len(quantities) else "1"),
                unit=Unit(units[i]) if i < len(units) else Unit.pcs,
                source="ingest",
            ),
        )
    return RedirectResponse("/", status_code=303)


def _review(request: Request, result, db: Session):
    return templates.TemplateResponse(
        "ingest_review.html",
        {"request": request, "result": result, "units": list(Unit)},
    )


def _to_float(value: str) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return 1.0
