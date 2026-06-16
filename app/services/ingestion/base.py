"""Базовые абстракции слоя ингестии: единый результат, интерфейсы и разбор LLM-ответа."""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from pydantic import ValidationError

from app.schemas import ParsedProduct

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Результат разбора любого источника ввода."""
    products: list[ParsedProduct] = field(default_factory=list)
    raw_text: str | None = None          # распознанный текст (для STT) или сырой ответ
    configured: bool = True              # False → провайдер не настроен (показываем в UI)
    message: str | None = None           # пояснение/ошибка для пользователя


class TextParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> IngestResult: ...


class VisionProvider(ABC):
    @abstractmethod
    def parse_image(self, image_bytes: bytes, mime_type: str) -> IngestResult: ...


class SttProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, filename: str) -> IngestResult: ...


def build_prompt(today: date | None = None) -> str:
    """Системный промпт для LLM (vision и text): полная карточка + разрешение относительных дат."""
    today = today or date.today()
    return (
        "Ты помощник для учёта продуктов в холодильнике. "
        f"Сегодняшняя дата: {today.isoformat()}. "
        "Определи продукты и верни СТРОГО JSON-объект {\"products\": [...]}, где каждый элемент: "
        '{"name": "строка", "quantity": число, "unit": "шт|г|кг|мл|л", '
        '"category": "строка или null", "production_date": "YYYY-MM-DD или null", '
        '"expiry_date": "YYYY-MM-DD или null", "days_after_opening": "целое или null"}. '
        "Разрешай относительные даты относительно сегодняшней («вчера», «годен 5 дней» → "
        "expiry_date = сегодня + 5 дней). Если данных нет — ставь null. "
        "Не добавляй пояснений, только JSON."
    )


def parse_llm_json(content: str) -> list[ParsedProduct]:
    """Достаёт массив продуктов из ответа LLM (учитывает обёртку {"products": [...]})."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Не удалось распарсить JSON от LLM: %s", content[:200])
        return []
    if isinstance(data, dict):
        for key in ("products", "items", "data"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [data]
    products: list[ParsedProduct] = []
    for item in data if isinstance(data, list) else []:
        try:
            products.append(ParsedProduct.model_validate(item))
        except ValidationError:
            logger.warning("Пропущена невалидная позиция от LLM: %s", item)
    return products
