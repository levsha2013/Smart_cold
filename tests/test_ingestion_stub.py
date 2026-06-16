"""Тесты слоя ингестии: текстовый парсер и graceful-заглушки vision/STT без ключей."""
from __future__ import annotations

import pytest

from app.config import settings
from app.models import Unit
from app.services.ingestion import factory
from app.services.ingestion.text import rule_parser


@pytest.fixture()
def no_keys(monkeypatch):
    """Обнуляет API-ключи, чтобы проверить ветку заглушек независимо от .env пользователя."""
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")


def test_text_parser_quantity_and_unit():
    result = rule_parser.parse("молоко 2 л\nяйца 10 шт\nхлеб")
    assert result.configured is True
    assert len(result.products) == 3

    milk = result.products[0]
    assert milk.name.lower().startswith("молоко")
    assert milk.quantity == 2.0
    assert milk.unit == Unit.l

    eggs = result.products[1]
    assert eggs.quantity == 10.0
    assert eggs.unit == Unit.pcs

    bread = result.products[2]
    assert bread.quantity == 1.0  # без количества → 1 шт по умолчанию


def test_text_parser_comma_separated():
    result = rule_parser.parse("сыр 200 г, сок 1 л")
    assert len(result.products) == 2


def test_vision_stub_without_key(no_keys):
    # Без OPENROUTER_API_KEY провайдер — заглушка.
    result = factory.parse_image(b"fakebytes", "image/jpeg")
    assert result.configured is False
    assert "OPENROUTER" in (result.message or "")


def test_stt_stub_without_key(no_keys):
    result = factory.transcribe(b"fakeaudio", "voice.ogg")
    assert result.configured is False
    assert "GROQ" in (result.message or "")
