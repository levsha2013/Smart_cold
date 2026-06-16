"""Распознавание продуктов по фото через OpenRouter (OpenAI-совместимый chat/completions).

Без OPENROUTER_API_KEY работает как заглушка: возвращает configured=False, ничего не вызывая.
"""
from __future__ import annotations

import base64
import logging
from datetime import date

import httpx

from app.config import settings
from app.services.ingestion.base import (
    IngestResult,
    VisionProvider,
    build_prompt,
    parse_llm_json,
)

logger = logging.getLogger(__name__)
_TIMEOUT = 60.0


class StubVisionProvider(VisionProvider):
    def parse_image(self, image_bytes: bytes, mime_type: str) -> IngestResult:
        return IngestResult(
            configured=False,
            message="Распознавание фото не настроено: задайте OPENROUTER_API_KEY в .env.",
        )


class OpenRouterVisionProvider(VisionProvider):
    def parse_image(self, image_bytes: bytes, mime_type: str) -> IngestResult:
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
        payload = {
            "model": settings.openrouter_vision_model,
            "messages": [
                {"role": "system", "content": build_prompt(date.today())},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Какие продукты на фото? Верни JSON-массив."},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
        try:
            resp = httpx.post(
                f"{settings.openrouter_base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            logger.exception("OpenRouter vision request failed")
            return IngestResult(configured=True, message=f"Ошибка запроса к OpenRouter: {exc}")

        products = parse_llm_json(content)
        return IngestResult(products=products, raw_text=content, configured=True)


def get_provider() -> VisionProvider:
    return OpenRouterVisionProvider() if settings.vision_enabled else StubVisionProvider()
