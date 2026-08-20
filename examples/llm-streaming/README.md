# LLM Streaming via Server-Sent Events (SSE)

A FastAPI endpoint that streams an LLM's response token-by-token to the
browser using SSE and `StreamingResponse`, plus a minimal `llm_client.py`
abstraction that keeps the actual provider call swappable.

Accompanies: [`docs/14-ai-api-engineering/streaming-llm-responses.md`](../../docs/14-ai-api-engineering/streaming-llm-responses.md)

## What This Demonstrates

- `GET /chat/stream?prompt=...` returns a `text/event-stream` response built
  with FastAPI's `StreamingResponse`, formatting each chunk as a proper SSE
  `data: {...}\n\n` event and closing with a `data: [DONE]\n\n` sentinel.
- Response headers (`Cache-Control: no-cache`, `X-Accel-Buffering: no`) that
  matter in production to stop reverse proxies from buffering the whole
  response before it reaches the client — see the "Production
  Considerations" section of the accompanying chapter.
- A generic, provider-agnostic `llm_client.stream_chat_completion()`
  abstraction: an async generator that yields text chunks. The real
  provider call is written out as a clearly-commented pseudo-implementation
  (`_stream_from_real_provider`) showing the shape of a streaming HTTP call
  against an Anthropic/OpenAI-compatible-style chat completion API — it is
  **not** wired to any specific SDK, since we can't assume which provider or
  credentials you have.
- A **credential-free fallback** (`_stream_simulated`): if `LLM_API_KEY` is
  not set, the client streams a canned response word-by-word so the whole
  example runs immediately without any provider account.
- A minimal `index.html` using the browser's native `EventSource` API to
  consume the stream with zero extra dependencies.

## Prerequisites

- Python 3.11+
- No LLM provider account required to run the demo (see above) — only
  needed if you wire up `_stream_from_real_provider` to a real API.

## How to Run

```bash
cd examples/llm-streaming
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: only needed for a real provider
uvicorn main:app --reload
```

Open <http://localhost:8000/> and submit a prompt — you'll see the
(simulated, by default) response stream in word-sized chunks. Or hit the
endpoint directly:

```bash
curl -N "http://localhost:8000/chat/stream?prompt=hello"
```

## Using a Real Provider

1. Set `LLM_API_KEY` (and optionally `LLM_MODEL`) in `.env`.
2. Open `llm_client.py` and replace the body of `_stream_from_real_provider`
   with a real call to your provider's SDK or streaming HTTP endpoint — the
   docstring in that function shows the general request/response shape
   (an `httpx`-based streaming POST reading `data:` lines) that most
   Anthropic/OpenAI-compatible-style chat completion APIs share. Adjust the
   URL, request body, and the field you pull incremental text out of to
   match your specific provider's actual response schema.
3. Restart the server — `stream_chat_completion` automatically switches to
   `_stream_from_real_provider` once `LLM_API_KEY` is set.

## Things to Try / Modify

1. **Add a heartbeat** — send a comment line (`: keep-alive\n\n`) every few
   seconds of silence in `sse_event_stream` to prevent idle-timeout
   disconnects on long gaps between tokens, as discussed in the chapter's
   exercises.
2. **Handle client disconnects** — confirm that closing the browser tab
   mid-stream stops the generator (add a `print` inside
   `sse_event_stream`'s loop and watch server logs when you close early).
   In a real provider integration, this is where you'd cancel the upstream
   HTTP request to avoid paying for generation nobody receives.
3. **Wire up tool-call buffering** — the chapter's `collect_streamed_tool_call`
   pattern (buffer fragments, parse once at completion) doesn't apply here
   since this endpoint only streams plain text — try extending
   `llm_client.py` with a second function that simulates streaming
   tool-call argument fragments and buffers them correctly.
