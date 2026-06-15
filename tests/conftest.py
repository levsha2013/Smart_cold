"""Фикстуры тестов: изолированная in-memory БД с засеянным словарём сроков."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Category, ShelfLifeBasis, ShelfLifeDefault, StorageLocation
from app.services import freshness

SEED = Path(__file__).resolve().parent.parent / "data" / "shelf_life.json"


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    session = Session()

    session.add_all([Category(name="Молочное"), Category(name="Прочее"), Category(name="Мясо и рыба")])
    session.add_all([StorageLocation(name="Холодильник")])
    for e in json.loads(SEED.read_text(encoding="utf-8")):
        session.add(
            ShelfLifeDefault(
                name_pattern=e["name_pattern"],
                category=e.get("category"),
                days=e["days"],
                basis=ShelfLifeBasis(e.get("basis", "production")),
                days_after_opening=e.get("days_after_opening"),
            )
        )
    session.commit()
    freshness._load_defaults(session)  # прогрев кэша словаря
    yield session
    session.close()
