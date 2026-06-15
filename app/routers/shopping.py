"""Роутер списка покупок."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.templating import templates

router = APIRouter()


@router.get("/shopping")
def shopping(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "shopping.html", {"request": request, "items": crud.list_shopping(db)}
    )


@router.post("/shopping")
def add_item(name: str = Form(...), db: Session = Depends(get_db)):
    name = name.strip()
    if name:
        crud.add_shopping_item(db, name)
    return RedirectResponse("/shopping", status_code=303)


@router.post("/shopping/{item_id}/toggle")
def toggle_item(item_id: int, db: Session = Depends(get_db)):
    crud.toggle_shopping_item(db, item_id)
    return RedirectResponse("/shopping", status_code=303)


@router.post("/shopping/{item_id}/delete")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    crud.delete_shopping_item(db, item_id)
    return RedirectResponse("/shopping", status_code=303)
