"""Текстовый разбор в полную карточку через OpenRouter (для транскрипта голоса и текста).

Без OPENROUTER_API_KEY — заглушка. Использует ту же схему/промпт, что и vision.
"""
from __future__ import annotations

import logging
from datetime import date

import httpx

from app.config import settings
from app.services.ingestion.base import (
    IngestResult,
    TextParser,
    build_prompt,
    parse_llm_json,
)

logger = logging.getLogger(__name__)
_TIMEOUT = 60.0


class OpenRouterTextProvider(TextParser):
    def parse(self, text: str) -> IngestResult:
        if not settings.openrouter_enabled:
            return IngestResult(
                configured=False,
                message="LLM-разбор не настроен: задайте OPENROUTER_API_KEY в .env.",
            )
        payload = {
            "model": settings.openrouter_text_model,
            "messages": [
                {"role": "system", "content": build_prompt(date.today())},
                {"role": "user", "content": text},
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
            logger.exception("OpenRouter text request failed")
            return IngestResult(configured=True, message=f"Ошибка запроса к OpenRouter: {exc}")

        products = parse_llm_json(content)
        return IngestResult(products=products, raw_text=text, configured=True)


# Singleton для переиспользования.
llm_text_parser = OpenRouterTextProvider()
