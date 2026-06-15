"""Отправка сообщений в Telegram. Без токена/chat_id — пишет в лог."""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
_TIMEOUT = 15.0


def send_message(text: str) -> bool:
    """Отправляет сообщение в Telegram. Возвращает True при успехе, False иначе."""
    if not settings.telegram_enabled:
        logger.info("[Telegram отключён] Сообщение:\n%s", text)
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
    payload = {"chat_id": settings.telegram_chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = httpx.post(url, json=payload, timeout=_TIMEOUT)
        resp.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Не удалось отправить сообщение в Telegram")
        return False
