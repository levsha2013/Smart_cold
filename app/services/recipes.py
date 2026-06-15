"""ЗАГЛУШКА подбора рецептов. Позже здесь будет вызов LLM по наличию продуктов."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app import crud


@dataclass
class RecipeSuggestion:
    title: str
    instructions: str
    used: list[str]


def suggest_recipes(db: Session) -> list[RecipeSuggestion]:
    """Пока возвращает пустой список — интерфейс готов под будущую LLM-интеграцию.

    Планируемая логика: взять список продуктов (crud.list_products), отправить в LLM
    запрос на рецепты из доступных ингредиентов, распарсить ответ в RecipeSuggestion.
    """
    _ = crud.list_products(db)  # задел: ингредиенты для будущего промпта
    return []


def is_configured() -> bool:
    return False
