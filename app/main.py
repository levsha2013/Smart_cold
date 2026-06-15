"""Точка входа FastAPI: подключение роутеров, статики, инициализация БД и планировщика."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import history, ingest, products, recipes, shopping
from app.services.scheduler import shutdown_scheduler, start_scheduler

logging.basicConfig(level=logging.INFO)

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Smart Holodilnik", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(products.router)
app.include_router(shopping.router)
app.include_router(history.router)
app.include_router(recipes.router)
app.include_router(ingest.router)


@app.get("/health")
def health():
    return {"status": "ok"}
