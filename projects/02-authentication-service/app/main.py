"""FastAPI application entrypoint for the standalone Authentication Service.

Run it:
    uvicorn app.main:app --reload

Note: OAuth social login and a JWKS/RS256 endpoint are marked optional /
advanced-improvement items in this project's README and are not
implemented here; this reference implementation covers the required
register/login/refresh-rotation/logout/password-reset/RBAC flow.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Authentication Service", version="1.0.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
