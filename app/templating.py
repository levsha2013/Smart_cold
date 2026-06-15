"""Общий экземпляр Jinja2Templates с зарегистрированными хелперами."""
from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.services import freshness

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Хелперы, доступные во всех шаблонах.
templates.env.globals["assess"] = freshness.assess
templates.env.globals["STATUS_LABELS"] = freshness.STATUS_LABELS
