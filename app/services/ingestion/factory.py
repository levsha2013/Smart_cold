"""Единая точка получения провайдеров ингестии (выбор реальный/заглушка по config)."""
from __future__ import annotations

from app.services.ingestion import stt, vision
from app.services.ingestion.base import IngestResult, SttProvider, VisionProvider
from app.services.ingestion.text import rule_parser


def get_vision_provider() -> VisionProvider:
    return vision.get_provider()


def get_stt_provider() -> SttProvider:
    return stt.get_provider()


def parse_text(text: str) -> IngestResult:
    return rule_parser.parse(text)


def parse_image(image_bytes: bytes, mime_type: str) -> IngestResult:
    return get_vision_provider().parse_image(image_bytes, mime_type)


def transcribe(audio_bytes: bytes, filename: str) -> IngestResult:
    return get_stt_provider().transcribe(audio_bytes, filename)
