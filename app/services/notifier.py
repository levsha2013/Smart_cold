"""Формирование и отправка дайджеста об истекающих/истёкших продуктах."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app import crud
from app.services import freshness, telegram

logger = logging.getLogger(__name__)


def build_digest(db: Session) -> str | None:
    """Собирает текст дайджеста. Возвращает None, если нечего сообщать."""
    expiring: list[tuple] = []
    expired: list[tuple] = []
    for product in crud.list_products(db):
        f = freshness.assess(product)
        if f.status == freshness.EXPIRED:
            expired.append((product, f))
        elif f.status == freshness.EXPIRING:
            expiring.append((product, f))

    if not expiring and not expired:
        return None

    lines = ["🧊 <b>Холодильник: проверка сроков</b>", ""]
    if expired:
        lines.append("🔴 <b>Просрочено:</b>")
        for p, f in expired:
            lines.append(f"• {p.name} — истёк {abs(f.days_left)} дн. назад")
        lines.append("")
    if expiring:
        lines.append("🟡 <b>Скоро испортится:</b>")
        for p, f in expiring:
            suffix = "сегодня" if f.days_left == 0 else f"через {f.days_left} дн."
            lines.append(f"• {p.name} — {suffix}")
    return "\n".join(lines).strip()


def run_digest(db: Session) -> bool:
    """Формирует и отправляет дайджест. Возвращает True, если что-то отправлено."""
    text = build_digest(db)
    if text is None:
        logger.info("Дайджест: истекающих продуктов нет.")
        return False
    return telegram.send_message(text)
