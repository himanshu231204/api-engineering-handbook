"""
Background job queue + worker example.

A FastAPI endpoint enqueues "slow work" instead of doing it inline, a
background worker task (running inside the same process's asyncio event
loop) processes jobs one at a time from an `asyncio.Queue`, and a
status-check endpoint reports each job's lifecycle: pending -> processing ->
done / failed.

This is intentionally the SIMPLEST possible version of the pattern, useful
for understanding the shape of "enqueue now, process later, poll for
status." Real systems reach for Celery, RQ, or a managed queue like SQS
instead of `asyncio.Queue`, because those give you durability across
restarts, multiple worker processes/machines, retries, and dead-letter
queues — none of which this in-memory example has. See
../../docs/08-async-systems/message-queues.md for the production version of
this idea.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

import asyncio
import random
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Job(BaseModel):
    id: str
    status: JobStatus
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str
    updated_at: str


class EnqueueRequest(BaseModel):
    # Whatever the "slow work" needs as input. Kept generic for the demo —
    # a real endpoint would model this with a specific schema.
    data: dict[str, Any] = Field(default_factory=dict)


class EnqueueResponse(BaseModel):
    job_id: str
    status: JobStatus


# --- In-memory job store + queue -------------------------------------------
#
# `jobs` holds the current state of every job so GET /jobs/{id} has
# something to read. `queue` is the actual work queue a background worker
# task consumes from. Both live only in process memory: restart the process
# and every job (and its history) is gone. A real implementation persists
# job state in a database or the queue's own broker (Redis, SQS, RabbitMQ)
# specifically so it survives restarts and can be picked up by a *different*
# worker process than the one that enqueued it.

jobs: dict[str, Job] = {}
queue: asyncio.Queue[str] = asyncio.Queue()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def do_slow_work(payload: dict[str, Any]) -> dict[str, Any]:
    """Stand-in for whatever expensive operation you're offloading:
    resizing an image, calling a third-party API, generating a report, an
    LLM call, etc. Simulated here with a random delay and a small chance of
    failure so the status endpoint has something interesting to show.
    """
    await asyncio.sleep(random.uniform(1.0, 3.0))

    if payload.get("fail") is True:
        raise RuntimeError("simulated failure requested via payload.fail")

    return {"echo": payload, "processed": True}


async def worker(name: str) -> None:
    """Pulls job ids off the queue and processes them one at a time.

    Run several of these concurrently (see the lifespan handler below) to
    get simple parallelism — each `worker()` call is an independent
    consumer competing for items on the same `asyncio.Queue`.
    """
    while True:
        job_id = await queue.get()
        job = jobs.get(job_id)
        if job is None:
            queue.task_done()
            continue

        job.status = JobStatus.PROCESSING
        job.updated_at = _now()

        try:
            result = await do_slow_work(job.payload)
        except Exception as exc:  # noqa: BLE001 - demo: surface any failure on the job
            job.status = JobStatus.FAILED
            job.error = str(exc)
        else:
            job.status = JobStatus.DONE
            job.result = result
        finally:
            job.updated_at = _now()
            queue.task_done()


WORKER_COUNT = 2
_worker_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    for i in range(WORKER_COUNT):
        _worker_tasks.append(asyncio.create_task(worker(f"worker-{i}")))
    yield
    for task in _worker_tasks:
        task.cancel()
    await asyncio.gather(*_worker_tasks, return_exceptions=True)


app = FastAPI(title="Background Jobs Example", lifespan=lifespan)


@app.post("/jobs", response_model=EnqueueResponse, status_code=202)
async def enqueue_job(request: EnqueueRequest) -> EnqueueResponse:
    """Enqueue a job and return immediately with 202 Accepted + a job id.

    The caller polls GET /jobs/{id} to find out when it's done, instead of
    the request blocking until the slow work finishes.
    """
    job_id = str(uuid.uuid4())
    now = _now()
    jobs[job_id] = Job(
        id=job_id,
        status=JobStatus.PENDING,
        payload=request.data,
        created_at=now,
        updated_at=now,
    )
    await queue.put(job_id)
    return EnqueueResponse(job_id=job_id, status=JobStatus.PENDING)


@app.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str) -> Job:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/jobs", response_model=list[Job])
async def list_jobs() -> list[Job]:
    return list(jobs.values())
