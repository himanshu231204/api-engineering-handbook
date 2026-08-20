# Minimal RAG (Retrieval-Augmented Generation) API

A small but complete, end-to-end RAG pipeline: ingest text, chunk it,
embed the chunks, store the vectors in memory, and query it with retrieval
+ context construction + a (stubbed) LLM call. Runs immediately with **no
external API keys** using local fallbacks — see below for how to swap in
real embedding and LLM providers.

Accompanies: [`docs/16-rag-apis/README.md`](../../docs/16-rag-apis/README.md)
(and specifically
[`chunking-pipelines.md`](../../docs/16-rag-apis/chunking-pipelines.md),
[`embedding-apis.md`](../../docs/16-rag-apis/embedding-apis.md),
[`vector-database-apis.md`](../../docs/16-rag-apis/vector-database-apis.md),
[`retrieval.md`](../../docs/16-rag-apis/retrieval.md), and
[`context-construction.md`](../../docs/16-rag-apis/context-construction.md))

## What This Demonstrates

- **`chunking.py`** — a simple fixed-size, whitespace-aware, overlapping
  text chunker (`chunk_text`).
- **`vector_store.py`**:
  - `embed()` — a generic embedding function. If `EMBEDDING_API_KEY` is set,
    it routes to `_embed_via_api`, a clearly-commented pseudo-implementation
    showing the shape of a real embedding API call. Otherwise it falls back
    to `_embed_local_bag_of_words`, a tiny dependency-free feature-hashing
    bag-of-words embedding — enough to demonstrate the retrieval mechanics
    (and to see semantically-similar text score higher) without any
    external service.
  - `VectorStore` — an in-memory list of vectors plus brute-force cosine
    similarity search. No vector database dependency required.
- **`main.py`**:
  - `POST /ingest` and `POST /ingest/file` — chunk + embed + store text.
  - `POST /query` — embed the question, retrieve the top-k most similar
    chunks, concatenate them into a context string (`build_context`), and
    call `call_llm()` to produce an answer grounded in that context.
    `call_llm()` follows the same pattern as `embed()`: a real-provider
    pseudo-implementation behind an `LLM_API_KEY` check, and a simple
    extractive fallback (returns the top chunk) when no key is set.
  - `GET /stats` — how many chunks are currently stored.

## Prerequisites

- Python 3.11+
- No external accounts required to run the demo end-to-end.

## How to Run

```bash
cd examples/rag-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: only needed for real embedding/LLM providers
uvicorn main:app --reload
```

Ingest a document:

```bash
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
        "text": "FastAPI is a modern Python web framework for building APIs. It uses Pydantic for data validation and generates OpenAPI docs automatically. Rate limiting protects an API from abuse by capping how many requests a client can make in a time window.",
        "source": "notes.txt"
      }'
```

Or ingest a file:

```bash
curl -s -X POST http://localhost:8000/ingest/file -F "file=@notes.txt"
```

Query it:

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "what does rate limiting do?", "top_k": 2}'
```

You should see the chunk about rate limiting retrieved with the highest
similarity score, and a (simulated, since no `LLM_API_KEY` is set) answer
built from it.

## Using Real Embedding / LLM Providers

1. Set `EMBEDDING_API_KEY` and/or `LLM_API_KEY` in `.env`.
2. In `vector_store.py`, implement `_embed_via_api()` following the shape
   shown in its docstring (a generic `httpx` POST to an embeddings
   endpoint) — adjust the URL and response parsing for your actual
   provider.
3. In `main.py`, implement the real-call branch of `call_llm()` the same
   way, following its docstring.
4. **Important**: if you add a real embedding provider, re-ingest your
   documents — vectors produced by the local bag-of-words fallback and a
   real embedding model are not comparable, so a store can't mix the two.

## Things to Try / Modify

1. **Watch retrieval quality with the local embedder** — ingest two
   unrelated paragraphs and confirm a query about one topic scores that
   paragraph's chunks higher. Then try a query using synonyms instead of
   exact words from the text, and notice the bag-of-words fallback's main
   limitation: it only captures keyword overlap, not meaning.
2. **Tune chunking** — change `chunk_size`/`chunk_overlap` in `main.py`'s
   `_ingest()` and observe how retrieval granularity changes for a longer
   document.
3. **Swap the vector store for a real one** — sketch (or implement) how
   `VectorStore.add`/`search` would change if backed by `pgvector` or a
   managed vector database instead of a Python list, per
   [`docs/16-rag-apis/vector-database-apis.md`](../../docs/16-rag-apis/vector-database-apis.md).
4. **Add reranking** — after `store.search()` returns the top-k chunks by
   embedding similarity, add a second-pass reranking step (even a simple
   keyword-overlap boost) per
   [`docs/16-rag-apis/reranking.md`](../../docs/16-rag-apis/reranking.md).
