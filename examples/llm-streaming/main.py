"""
FastAPI endpoint that streams an LLM response token-by-token via
Server-Sent Events (SSE), using `StreamingResponse`.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

import json

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse

from llm_client import stream_chat_completion

app = FastAPI(title="LLM Streaming (SSE) Example")


@app.get("/")
async def index() -> FileResponse:
    """Serve the minimal HTML/JS test page (uses EventSource)."""
    return FileResponse("index.html")


async def sse_event_stream(prompt: str):
    """Wrap `stream_chat_completion` chunks as proper SSE `data:` events.

    Each event is a JSON object on a single `data:` line, terminated by a
    blank line (`\\n\\n`) as the SSE spec requires. A final
    `data: [DONE]\\n\\n` sentinel tells the client the stream is complete —
    a common convention (not part of the SSE spec itself) so clients don't
    have to rely solely on the connection closing to know they're done.
    """
    try:
        async for chunk in stream_chat_completion(prompt):
            payload = json.dumps({"text": chunk})
            yield f"data: {payload}\n\n"
    except Exception as exc:  # noqa: BLE001 - surface the error to the client, then close
        error_payload = json.dumps({"error": str(exc)})
        yield f"data: {error_payload}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@app.get("/chat/stream")
async def chat_stream(prompt: str = Query(..., min_length=1)) -> StreamingResponse:
    return StreamingResponse(
        sse_event_stream(prompt),
        media_type="text/event-stream",
        headers={
            # Prevent intermediary proxies from buffering the whole
            # response before it reaches the client, which would silently
            # defeat streaming. See:
            # ../../docs/14-ai-api-engineering/streaming-llm-responses.md
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
