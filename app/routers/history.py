"""Роутер истории событий."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.templating import templates

router = APIRouter()

ACTION_LABELS = {
    "added": "➕ Добавлено",
    "consumed": "➖ Списано",
    "removed": "🗑 Удалено",
    "expired": "⏰ Просрочено",
    "opened": "📂 Вскрыто",
}


@router.get("/history")
def history(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "events": crud.list_history(db), "labels": ACTION_LABELS},
    )
