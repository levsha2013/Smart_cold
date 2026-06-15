"""Роутер рецептов (заглушка)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import recipes as recipes_service
from app.templating import templates

router = APIRouter()


@router.get("/recipes")
def recipes(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "recipes.html",
        {
            "request": request,
            "suggestions": recipes_service.suggest_recipes(db),
            "configured": recipes_service.is_configured(),
        },
    )
