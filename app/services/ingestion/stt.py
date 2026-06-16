"""Распознавание речи через Groq Whisper (OpenAI-совместимый /audio/transcriptions).

Без GROQ_API_KEY работает как заглушка. Распознанный текст затем передаётся в text-парсер.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.services.ingestion.base import IngestResult, SttProvider
from app.services.ingestion.llm import llm_text_parser
from app.services.ingestion.text import rule_parser

logger = logging.getLogger(__name__)
_TIMEOUT = 60.0


class StubSttProvider(SttProvider):
    def transcribe(self, audio_bytes: bytes, filename: str) -> IngestResult:
        return IngestResult(
            configured=False,
            message="Распознавание речи не настроено: задайте GROQ_API_KEY в .env.",
        )


class GroqSttProvider(SttProvider):
    def transcribe(self, audio_bytes: bytes, filename: str) -> IngestResult:
        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
        files = {"file": (filename, audio_bytes)}
        data = {"model": settings.groq_stt_model, "language": "ru"}
        try:
            resp = httpx.post(
                f"{settings.groq_base_url}/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            text = resp.json().get("text", "").strip()
        except (httpx.HTTPError, KeyError) as exc:
            logger.exception("Groq STT request failed")
            return IngestResult(configured=True, message=f"Ошибка запроса к Groq: {exc}")

        # Транскрипт → полная карточка через LLM (если OpenRouter настроен),
        # иначе — простой regex-парсер (только имя/кол-во/единица).
        if settings.openrouter_enabled:
            parsed = llm_text_parser.parse(text)
        else:
            parsed = rule_parser.parse(text)
        parsed.raw_text = text
        return parsed


def get_provider() -> SttProvider:
    return GroqSttProvider() if settings.stt_enabled else StubSttProvider()
