# Background Jobs (Queue + Worker Pattern)

Demonstrates the fundamental shape of offloading slow work from a request:
enqueue a job and return immediately, process it in a background worker, and
let the client poll a status endpoint for the result.

Accompanies: [`docs/08-async-systems/background-tasks.md`](../../docs/08-async-systems/background-tasks.md)
and [`docs/08-async-systems/message-queues.md`](../../docs/08-async-systems/message-queues.md)

## What This Demonstrates

- `POST /jobs` enqueues a job and responds `202 Accepted` with a job id
  immediately — it does **not** wait for the work to finish.
- One or more background `worker()` coroutines, started at app startup via
  FastAPI's `lifespan`, pull job ids off an `asyncio.Queue` and process them
  concurrently.
- `GET /jobs/{id}` reports the job's current lifecycle state: `pending` ->
  `processing` -> `done` or `failed`.
- Failure handling: a job that raises is marked `failed` with the error
  message attached, instead of taking down the worker loop.

## Why Not Just Use `asyncio.Queue` in Production

This example intentionally uses the simplest possible primitives so the
*pattern* is easy to see. `asyncio.Queue` and the in-memory `jobs` dict both
live only inside this one process's memory:

- If the process restarts, every enqueued/in-flight job and its history is
  lost — nothing durable was ever written down.
- You can't run a second process (for more throughput, or for
  redundancy) and have it share the same queue.
- There's no retry policy, no dead-letter queue, no visibility timeout.

Real systems use **Celery**, **RQ**, or a managed queue like **SQS** (backed
by Redis, RabbitMQ, or a managed broker) specifically to get durability,
horizontal scaling across worker machines, and retry/backoff for free. See
[`docs/08-async-systems/message-queues.md`](../../docs/08-async-systems/message-queues.md)
for the production-grade version of this pattern.

## Prerequisites

- Python 3.11+

## How to Run

```bash
cd examples/background-jobs
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Enqueue a job:

```bash
curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"data": {"note": "resize an image"}}'
# -> {"job_id": "...", "status": "pending"}
```

Poll for its status (it takes 1-3 simulated seconds to finish):

```bash
curl -s http://localhost:8000/jobs/<job_id>
```

Trigger the simulated failure path:

```bash
curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"data": {"fail": true}}'
```

## Things to Try / Modify

1. **Watch concurrency** — enqueue 5-10 jobs at once and poll them; with
   `WORKER_COUNT = 2` you'll see at most two `processing` at a time. Change
   `WORKER_COUNT` and observe the difference.
2. **Add a `pending` count endpoint** — expose `queue.qsize()` via a small
   `/queue/stats` route to show backpressure building up under load.
3. **Simulate a crash** — restart the server mid-job and confirm the job
   (and its status) simply vanishes, illustrating exactly why a real queue
   needs durable storage instead of `asyncio.Queue`.
4. **Swap in a real queue** — sketch what changes if `queue.put()` became
   `celery_task.delay()` or a `boto3` SQS `send_message()` call, and the
   worker became a separate `celery worker` process instead of an
   in-process `asyncio.Task`.
