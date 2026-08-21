"""FastAPI application entrypoint for the Bookshelf CRUD API.

Run it:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.books import router as books_router
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.include_router(books_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
