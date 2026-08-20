"""
Application entrypoint: `uvicorn app.main:app --reload`.

Wires together configuration, database setup, middleware, exception
handlers, and routers -- this is the "project architecture" chapter made
concrete. See docs/03-building-apis/project-architecture.md.
"""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.exceptions import TaskNotFoundError
from app.routers import tasks

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: create tables if they don't exist. A real production service
    # would use a migration tool instead (see
    # docs/04-databases-and-apis/migrations.md) -- create_all is fine for a
    # from-scratch SQLite example.
    Base.metadata.create_all(bind=engine)
    yield
    # (nothing to clean up on shutdown for this example)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """A small custom middleware: times every request and reports it back
    as a response header. See docs/03-building-apis/middleware.md."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    """Translate a domain exception into an HTTP response in exactly one
    place, instead of every route handler doing its own try/except. See
    docs/03-building-apis/exception-handling.md."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": {"code": "task_not_found", "message": str(exc)}},
    )


app.include_router(tasks.router)


@app.get("/health", tags=["health"], summary="Liveness/readiness check")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}
