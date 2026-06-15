"""Базовые абстракции слоя ингестии: единый результат и интерфейсы провайдеров."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.schemas import ParsedProduct


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


# Системный промпт для LLM-провайдеров (vision и будущий text-LLM).
EXTRACTION_PROMPT = (
    "Ты помощник для учёта продуктов в холодильнике. "
    "Определи продукты и верни СТРОГО JSON-массив объектов вида "
    '[{"name": "строка", "quantity": число, "unit": "шт|г|кг|мл|л", "category": "строка или null"}]. '
    "Не добавляй пояснений, только JSON."
)
