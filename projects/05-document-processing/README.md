# Project 5 — Async Document Processing Pipeline

## Goal

Build an API where uploading a document doesn't return a finished result — it kicks off a background job, and the client polls (or subscribes) for status until processing completes. This is the project that makes "sync vs async" and "background tasks and job queues" concrete: you'll feel exactly why a request/response cycle is the wrong model for anything that takes more than a second or two. Deliberately, this project stops short of embeddings and retrieval — it's the async/queue foundation that Project 7 (Production RAG) builds directly on top of.

## Builds On

- [Part 8 — Async Systems](../../docs/08-async-systems/README.md)
- Specifically: [sync vs async](../../docs/08-async-systems/sync-vs-async.md), [Python asyncio](../../docs/08-async-systems/python-asyncio.md), [background tasks](../../docs/08-async-systems/background-tasks.md), [message queues](../../docs/08-async-systems/message-queues.md)
- Related, for the upload side: [file upload architecture](../../docs/16-rag-apis/file-upload-architecture.md), [document ingestion APIs](../../docs/16-rag-apis/document-ingestion-apis.md)

## Requirements

- Clients upload a document (PDF, TXT, or DOCX) via multipart upload; the API immediately returns a `document_id` and status `queued` — it does not block on processing.
- A background worker picks up queued documents, extracts text, and splits it into chunks (simple fixed-size or paragraph-based chunking is enough — no embeddings yet).
- Document status progresses through a well-defined state machine: `queued` → `processing` → `completed` or `failed`, with a `failure_reason` on failure.
- Clients can poll `GET /documents/{id}` to check status and, once completed, retrieve extracted chunk metadata (chunk count, character count, preview).
- Processing is retried automatically on transient failures (e.g., simulate a flaky parser) with a bounded retry count before moving to `failed`.
- Large or malformed files are rejected at upload time with a clear 4xx error, not silently queued to fail later.
- The system can process multiple documents concurrently without one large document blocking others (this is the core async lesson).
- An admin/debug endpoint shows queue depth and worker health.

## Architecture

```mermaid
flowchart LR
    Client[Client] -->|multipart upload| API[Upload API]
    API --> Storage[(Object Storage /\nLocal Disk for docs)]
    API --> DocDB[(documents table)]
    API -->|enqueue job| Queue[(Job Queue\nRedis/RQ or Celery)]
    Queue --> Worker1[Worker]
    Queue --> Worker2[Worker]
    Worker1 --> Extractor[Text Extractor\n(pdf/docx/txt parser)]
    Extractor --> Chunker[Chunking Pipeline]
    Chunker --> ChunkDB[(chunks table)]
    Worker1 -->|update status| DocDB
    Client -->|GET /documents/id| API
    API -->|read status| DocDB
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/documents` | Upload a document (multipart/form-data). Validates type/size, stores file, enqueues processing job, returns 202 + `document_id`. |
| GET | `/documents/{id}` | Get current status, metadata, and (if completed) chunk summary. |
| GET | `/documents/{id}/chunks` | List extracted chunks for a completed document, paginated. |
| DELETE | `/documents/{id}` | Delete a document and its stored file/chunks. |
| GET | `/documents` | List the user's documents with status filter (`queued`, `processing`, `completed`, `failed`). |
| POST | `/documents/{id}/reprocess` | Re-enqueue a failed document for another processing attempt. |
| GET | `/admin/queue` | Debug endpoint: current queue depth, in-flight job count, worker heartbeat. |

## Database Schema

```sql
CREATE TABLE documents (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL,
    filename       TEXT NOT NULL,
    content_type   TEXT NOT NULL,
    size_bytes     INTEGER NOT NULL,
    storage_path   TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued','processing','completed','failed')),
    failure_reason TEXT,
    attempt_count  INTEGER NOT NULL DEFAULT 0,
    max_attempts   INTEGER NOT NULL DEFAULT 3,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at   TIMESTAMPTZ
);

CREATE TABLE chunks (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index    INTEGER NOT NULL,
    content        TEXT NOT NULL,
    char_count     INTEGER NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE processing_jobs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','succeeded','failed')),
    worker_id      TEXT,
    started_at     TIMESTAMPTZ,
    finished_at    TIMESTAMPTZ,
    error          TEXT
);
```

## Suggested Folder Structure

```
05-document-processing/
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── documents.py
│   │   └── admin.py
│   ├── schemas/
│   │   └── document.py
│   ├── services/
│   │   ├── upload_service.py
│   │   └── document_service.py
│   ├── workers/
│   │   ├── worker.py               # queue consumer entrypoint
│   │   ├── extractor.py            # pdf/docx/txt -> raw text
│   │   └── chunker.py
│   ├── queue/
│   │   └── client.py               # Redis/RQ or Celery wrapper
│   ├── models/
│   │   ├── document.py
│   │   └── chunk.py
│   ├── storage/
│   │   └── local_storage.py
│   ├── db/session.py
│   └── core/config.py
├── tests/
│   ├── test_upload_validation.py
│   ├── test_status_transitions.py
│   ├── test_chunking.py
│   └── test_retry_on_failure.py
├── requirements.txt
├── docker-compose.yml               # api + worker + redis + postgres
└── README.md
```

## Step-by-Step Implementation Plan

1. Scaffold FastAPI project with Postgres, Redis, and a Docker Compose file running `api` and `worker` as separate services.
2. Implement `POST /documents`: accept multipart upload, validate content-type and max size, save file to local/object storage, insert a `documents` row with status `queued`.
3. Set up a job queue (RQ, Celery, or a hand-rolled Redis list) and enqueue a processing job referencing the `document_id` immediately after upload, per [background tasks](../../docs/08-async-systems/background-tasks.md) and [message queues](../../docs/08-async-systems/message-queues.md).
4. Build the worker entrypoint that consumes jobs, marks the document `processing`, and calls the extractor.
5. Implement the text extractor for at least TXT and PDF (e.g. `pypdf`), returning raw text or raising a clear parsing error.
6. Implement a simple chunker (fixed character window with overlap, or paragraph-based split) and persist rows to `chunks`.
7. On success, mark the document `completed` with `completed_at` set; on failure, increment `attempt_count`, and either re-enqueue (if under `max_attempts`) or mark `failed` with `failure_reason`.
8. Implement `GET /documents/{id}` to expose status, and once `completed`, chunk count/char count without returning full chunk content (keep that in the dedicated chunks endpoint).
9. Implement `GET /documents/{id}/chunks` with pagination.
10. Simulate transient failures (e.g., a `FLAKY_PARSER=true` env flag that randomly throws) to prove the retry path actually works end to end, not just in theory.
11. Implement `POST /documents/{id}/reprocess` to manually reset a failed document back into the queue.
12. Add `GET /admin/queue` reporting queue depth and worker liveness (e.g. a heartbeat key in Redis updated by each worker).
13. Write concurrency tests: enqueue several documents at once and assert they complete independently (one artificially slow document doesn't block the others).

## Advanced Improvements

- Replace local disk storage with S3-compatible object storage and generate pre-signed upload URLs.
- Add a WebSocket or Server-Sent Events status stream so clients don't have to poll, per [Server-Sent Events](../../docs/09-realtime-and-webhooks/server-sent-events.md).
- Add OCR support for scanned/image-based PDFs.
- Add per-user concurrency limits so one user can't monopolize all workers.
- Add a priority queue (paid tier documents processed before free tier).
- Swap the hand-rolled retry logic for Celery's native retry/backoff support and compare the two approaches.

## Production Checklist

- [ ] Upload size and content-type strictly validated server-side, not just trusted from the client.
- [ ] Uploaded files scanned or sandboxed before parsing (malicious PDFs/DOCX are a real attack surface).
- [ ] Worker processing is idempotent — re-running a job for the same document doesn't duplicate chunks (upsert or delete-then-insert).
- [ ] Bounded retry count with backoff before permanent failure; no infinite retry loops.
- [ ] Dead documents (repeatedly failing) are visible to an operator, not silently stuck in `queued`.
- [ ] Worker health/heartbeat monitored; queue depth alerting configured for backlog buildup.
- [ ] Storage cleanup: deleting a document removes its file from storage, not just the DB row.
- [ ] Resource limits on the worker (max file size processed, timeout per document) to prevent one bad file from hanging a worker indefinitely.
- [ ] Structured logging with `document_id` correlation across upload → queue → worker → completion.
- [ ] Horizontal scaling story documented: workers are stateless and can be scaled independently of the API.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Foundation for: [Project 7 — Production RAG API](../07-production-rag/README.md)
