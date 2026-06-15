"""Подключение к БД, сессии и инициализация (создание таблиц + сидирование справочников)."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# SQLite требует check_same_thread=False для работы в многопоточном FastAPI/APScheduler.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SHELF_LIFE_SEED = DATA_DIR / "shelf_life.json"


def get_db():
    """FastAPI dependency: выдаёт сессию и гарантированно закрывает её."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создаёт таблицы и сидирует справочники, если они пусты."""
    from app import models  # импорт здесь, чтобы избежать циклов

    models.Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _seed_categories(db)
        _seed_locations(db)
        _seed_shelf_life(db)
        db.commit()
        # Прогреваем кэш словаря сроков для freshness (используется без сессии).
        from app.services import freshness

        freshness._load_defaults(db)


def _seed_categories(db: Session) -> None:
    from app.models import Category

    if db.query(Category).count() > 0:
        return
    defaults = ["Молочное", "Мясо и рыба", "Овощи и фрукты", "Бакалея", "Напитки", "Заморозка", "Прочее"]
    db.add_all([Category(name=name) for name in defaults])


def _seed_locations(db: Session) -> None:
    from app.models import StorageLocation

    if db.query(StorageLocation).count() > 0:
        return
    defaults = ["Холодильник", "Морозилка", "Полка", "Кладовая"]
    db.add_all([StorageLocation(name=name) for name in defaults])


def _seed_shelf_life(db: Session) -> None:
    from app.models import ShelfLifeDefault

    if db.query(ShelfLifeDefault).count() > 0:
        return
    if not SHELF_LIFE_SEED.exists():
        logger.warning("Файл словаря сроков не найден: %s", SHELF_LIFE_SEED)
        return
    entries = json.loads(SHELF_LIFE_SEED.read_text(encoding="utf-8"))
    for e in entries:
        db.add(
            ShelfLifeDefault(
                name_pattern=e["name_pattern"],
                category=e.get("category"),
                days=e["days"],
                basis=e.get("basis", "production"),
                days_after_opening=e.get("days_after_opening"),
            )
        )
