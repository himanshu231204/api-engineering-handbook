"""FastAPI application entrypoint for the Webhook Processing System.

Run it:
    uvicorn app.main:app --reload

The delivery worker (app/workers/delivery_worker.py) is not wired to a
standing background loop here -- see that module's docstring for why, and
call `attempt_delivery` from a scheduler/cron/task-queue in a real
deployment.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.deliveries import router as deliveries_router
from app.api.routes.inbound import router as inbound_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Webhook Processing System", version="1.0.0", lifespan=lifespan)
app.include_router(inbound_router)
app.include_router(subscriptions_router)
app.include_router(deliveries_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
