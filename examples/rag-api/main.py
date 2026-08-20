"""
Minimal end-to-end RAG (Retrieval-Augmented Generation) API.

Pipeline:
  POST /ingest  -> chunk text -> embed each chunk -> store in-memory
  POST /query   -> embed the question -> retrieve top-k similar chunks
                   -> build a context string -> (stubbed) LLM call -> answer

Runs entirely with local, dependency-free fallbacks by default (see
vector_store.py) so you can `pip install -r requirements.txt` and try the
whole pipeline immediately with no API keys. See the README for how to
swap in a real embedding API and a real LLM provider.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

import os
import uuid

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

from chunking import chunk_text
from vector_store import VectorStore

app = FastAPI(title="Minimal RAG API Example")
store = VectorStore()

LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "example-model-v1")


# --- Schemas -----------------------------------------------------------

class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = Field(default="inline-text")


class IngestResponse(BaseModel):
    source: str
    chunks_ingested: int
    total_chunks_in_store: int


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class RetrievedChunk(BaseModel):
    text: str
    source: str
    chunk_index: int
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    retrieved: list[RetrievedChunk]


# --- Ingestion -----------------------------------------------------------

def _ingest(text: str, source: str) -> IngestResponse:
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    for chunk in chunks:
        store.add(id=str(uuid.uuid4()), text=chunk.text, source=source, chunk_index=chunk.index)
    return IngestResponse(source=source, chunks_ingested=len(chunks), total_chunks_in_store=len(store))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_text(request: IngestTextRequest) -> IngestResponse:
    """Ingest raw text supplied directly in the request body."""
    return _ingest(request.text, request.source)


@app.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile) -> IngestResponse:
    """Ingest a small plain-text file upload.

    Kept simple (reads the whole file into memory) since this is a demo.
    See ../../docs/16-rag-apis/file-upload-architecture.md and
    ../../docs/16-rag-apis/async-document-processing.md for how a
    production ingestion endpoint handles large files (streamed uploads,
    async processing off the request path, object storage) instead.
    """
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="file must be UTF-8 text") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="file is empty")

    return _ingest(text, source=file.filename or "uploaded-file")


# --- Query (retrieval + context construction + LLM call) -----------------

def build_context(retrieved: list[RetrievedChunk]) -> str:
    """Assemble retrieved chunks into a single context string for the LLM
    prompt. See ../../docs/16-rag-apis/context-construction.md for
    strategies beyond simple concatenation (e.g. dedup, ordering,
    citation markers, token-budget trimming)."""
    parts = []
    for i, chunk in enumerate(retrieved, start=1):
        parts.append(f"[{i}] (source: {chunk.source}) {chunk.text}")
    return "\n\n".join(parts)


def call_llm(question: str, context: str) -> str:
    """Generate an answer grounded in the retrieved context.

    If `LLM_API_KEY` is configured, this is where a real call to an
    Anthropic/OpenAI-compatible-style chat completion API would go, e.g.:

        import httpx

        prompt = (
            "Answer the question using only the context below. If the "
            "context doesn't contain the answer, say so.\\n\\n"
            f"Context:\\n{context}\\n\\nQuestion: {question}"
        )
        response = httpx.post(
            "https://api.your-provider.example/v1/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    Without an API key, this falls back to a simple extractive "answer"
    (the top retrieved chunk) so the endpoint is runnable and demonstrably
    correct without any provider credentials. See
    ../../docs/14-ai-api-engineering/llm-apis.md and
    ../../docs/16-rag-apis/streaming-rag.md for the real generation step.
    """
    if LLM_API_KEY:
        raise NotImplementedError(
            "LLM_API_KEY is set, but call_llm() is still a stub. Plug in a "
            "real provider SDK/HTTP call here, following the shape "
            "described in this function's docstring."
        )

    if not context:
        return (
            "No relevant context was found in the vector store for this "
            "question. Ingest some documents first via POST /ingest."
        )

    return (
        "[simulated answer - no LLM_API_KEY configured] Based on the most "
        f"relevant retrieved chunk, here is a grounded excerpt for "
        f"\"{question}\":\n\n{context.splitlines()[0] if context else ''}"
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    results = store.search(request.question, top_k=request.top_k)

    retrieved = [
        RetrievedChunk(text=chunk.text, source=chunk.source, chunk_index=chunk.chunk_index, score=score)
        for chunk, score in results
    ]

    context = build_context(retrieved)
    answer = call_llm(request.question, context)

    return QueryResponse(question=request.question, answer=answer, retrieved=retrieved)


@app.get("/stats")
async def stats() -> dict:
    return {"total_chunks_in_store": len(store)}
