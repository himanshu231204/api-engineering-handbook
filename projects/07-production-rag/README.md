# Project 7 — Production RAG API

## Goal

Build a complete Retrieval-Augmented Generation pipeline as a production-shaped API: ingest documents, chunk and embed them, store vectors, retrieve and rerank relevant chunks for a query, and stream a cited answer back to the client. This project is where the async ingestion pattern from Project 5 meets the AI-specific concerns of Part 16 — embeddings, vector search, and grounding an LLM's answer in retrieved context instead of letting it hallucinate. By the end, you should be able to explain exactly which chunk of text justified each sentence of the model's answer.

## Builds On

- [Part 16 — RAG APIs](../../docs/16-rag-apis/README.md)
- Specifically: [document ingestion APIs](../../docs/16-rag-apis/document-ingestion-apis.md), [chunking pipelines](../../docs/16-rag-apis/chunking-pipelines.md), [embedding APIs](../../docs/16-rag-apis/embedding-apis.md), [vector database APIs](../../docs/16-rag-apis/vector-database-apis.md), [retrieval](../../docs/16-rag-apis/retrieval.md), [reranking](../../docs/16-rag-apis/reranking.md), [context construction](../../docs/16-rag-apis/context-construction.md), [streaming RAG](../../docs/16-rag-apis/streaming-rag.md), [async document processing](../../docs/16-rag-apis/async-document-processing.md)
- Reuses the ingestion/queue pattern from: [Project 5 — Async Document Processing Pipeline](../05-document-processing/README.md)
- Also draws on: [streaming LLM responses](../../docs/14-ai-api-engineering/streaming-llm-responses.md)

## Requirements

- Document upload and async processing pipeline (extend Project 5): extract text, chunk it, and now additionally embed each chunk and store the vector.
- A pluggable embedding provider client (start with one provider, e.g. OpenAI or a local sentence-transformers model) behind a thin interface so it can be swapped later.
- A vector store (start with a simple one — pgvector or an in-memory/FAISS index — abstracted behind a repository interface).
- `POST /query` accepts a natural-language question, embeds it, retrieves the top-K most relevant chunks, optionally reranks them, constructs a grounded prompt, and streams the LLM's answer back token-by-token.
- Every answer includes citations: which document/chunk IDs the answer was grounded in, so a client can show "sources."
- Retrieval is scoped per user/tenant — one user's documents never leak into another user's query results.
- If retrieval finds nothing sufficiently relevant, the API returns a clear "insufficient context" response instead of letting the LLM answer from parametric knowledge alone (or clearly flags that it did).
- Query and retrieval latency, token usage, and cost per query are logged for observability.

## Architecture

```mermaid
flowchart TB
    subgraph Ingestion
        Upload[POST /documents] --> Extract[Text Extraction]
        Extract --> Chunk[Chunking Pipeline]
        Chunk --> Embed[Embedding Provider]
        Embed --> VectorDB[(Vector Store\npgvector / FAISS)]
        Chunk --> ChunkDB[(chunks metadata)]
    end

    subgraph QueryTime
        Query[POST /query] --> QEmbed[Embed Query]
        QEmbed --> Retrieve[Vector Similarity Search]
        VectorDB --> Retrieve
        Retrieve --> Rerank[Reranker\n(cross-encoder or LLM-based)]
        Rerank --> ContextBuild[Context Construction\n(dedupe, truncate to token budget)]
        ContextBuild --> LLM[LLM Provider]
        LLM -->|streamed tokens| Client[Client / SSE]
        ContextBuild --> Citations[Citation Tracker]
        Citations --> Client
    end
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/documents` | Upload a document; enqueues extract → chunk → embed pipeline (extends Project 5). |
| GET | `/documents/{id}` | Status: `queued`, `processing`, `embedded`, `failed`. |
| DELETE | `/documents/{id}` | Delete a document and its chunks/vectors (must cascade into the vector store too). |
| POST | `/query` | Submit a question. Returns a streamed (SSE) response: retrieved chunk citations first, then the answer tokens. |
| GET | `/query/{query_id}` | Retrieve a past query's full answer, citations, and retrieval metadata (for debugging/audit). |
| GET | `/documents/{id}/chunks` | Inspect chunk-level metadata and embedding status for a document. |
| GET | `/collections` | List logical document collections/namespaces available to the authenticated tenant. |

## Database Schema

```sql
CREATE TABLE documents (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL,
    filename       TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued','processing','embedded','failed')),
    failure_reason TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id      UUID NOT NULL,          -- denormalized for fast, safe retrieval filtering
    chunk_index    INTEGER NOT NULL,
    content        TEXT NOT NULL,
    token_count    INTEGER NOT NULL,
    embedding      VECTOR(1536),            -- pgvector; dimension depends on embedding model
    embedded_at    TIMESTAMPTZ,
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_tenant ON chunks (tenant_id);

CREATE TABLE queries (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL,
    question       TEXT NOT NULL,
    answer         TEXT,
    retrieved_chunk_ids UUID[] NOT NULL DEFAULT '{}',
    retrieval_ms   INTEGER,
    generation_ms  INTEGER,
    prompt_tokens  INTEGER,
    completion_tokens INTEGER,
    estimated_cost_usd NUMERIC(10,6),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Suggested Folder Structure

```
07-production-rag/
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── documents.py
│   │   └── query.py
│   ├── schemas/
│   │   ├── document.py
│   │   └── query.py
│   ├── ingestion/
│   │   ├── extractor.py
│   │   ├── chunker.py
│   │   └── embedder.py           # provider-agnostic interface
│   ├── retrieval/
│   │   ├── vector_store.py       # pgvector/FAISS repository interface
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   └── context_builder.py
│   ├── generation/
│   │   ├── llm_client.py
│   │   └── prompt_templates.py
│   ├── workers/
│   │   └── ingestion_worker.py
│   ├── models/
│   │   ├── document.py
│   │   ├── chunk.py
│   │   └── query_log.py
│   ├── db/session.py
│   └── core/config.py
├── tests/
│   ├── test_chunking.py
│   ├── test_retrieval_tenant_isolation.py
│   ├── test_context_budget.py
│   └── test_citation_accuracy.py
├── requirements.txt
├── docker-compose.yml            # api + worker + postgres(pgvector) + redis
└── README.md
```

## Step-by-Step Implementation Plan

1. Start from Project 5's ingestion pipeline (upload → queue → extract → chunk); add pgvector to Postgres (or stand up FAISS) as the vector store.
2. Define the `Embedder` interface (`embed(texts: list[str]) -> list[vector]`) and implement one provider (OpenAI embeddings or a local sentence-transformers model), per [embedding APIs](../../docs/16-rag-apis/embedding-apis.md).
3. Extend the ingestion worker: after chunking, batch-embed chunks and store vectors alongside `tenant_id` for safe filtering, per [vector database APIs](../../docs/16-rag-apis/vector-database-apis.md).
4. Implement `POST /query`: embed the incoming question with the same embedder used for ingestion (embedding space must match).
5. Implement the retriever: top-K cosine similarity search scoped to `tenant_id`, per [retrieval](../../docs/16-rag-apis/retrieval.md) — write a test proving cross-tenant leakage is impossible even with a malicious query.
6. Add a reranking step (cross-encoder model or a cheap LLM-based relevance scorer) to reorder the top-K results before context construction, per [reranking](../../docs/16-rag-apis/reranking.md).
7. Implement context construction: dedupe overlapping chunks, truncate to a token budget, and format each chunk with a citation marker (`[1]`, `[2]`, ...), per [context construction](../../docs/16-rag-apis/context-construction.md).
8. Build the grounded prompt template that instructs the model to answer only from provided context and to cite sources inline, and to say so explicitly if the context is insufficient.
9. Implement streaming generation over SSE: stream citation metadata first (so the UI can render "Sources" immediately), then stream answer tokens as they arrive, per [streaming RAG](../../docs/16-rag-apis/streaming-rag.md) and [streaming LLM responses](../../docs/14-ai-api-engineering/streaming-llm-responses.md).
10. Log every query to the `queries` table with retrieval latency, generation latency, token counts, and estimated cost.
11. Add the "insufficient context" branch: if top-K similarity scores fall below a threshold, skip generation and return a clear message instead of forcing an answer.
12. Write an end-to-end test: ingest a known document, ask a question whose answer is only in that document, and assert both the answer content and the cited chunk IDs are correct.

## Advanced Improvements

- Add hybrid search (BM25 keyword + vector similarity) and compare recall/precision against vector-only search.
- Add query rewriting/expansion (e.g. HyDE) before retrieval to improve recall on short or ambiguous questions.
- Add semantic caching for repeated/similar queries, per [semantic caching](../../docs/15-production-ai-systems/semantic-caching.md).
- Add multi-document synthesis with per-sentence citation attribution.
- Add a feedback loop endpoint (`thumbs up/down` on an answer) to build an evaluation dataset over time.
- Swap the vector store for a dedicated engine (Qdrant, Pinecone, Weaviate) and compare operational tradeoffs against pgvector.

## Production Checklist

- [ ] Retrieval is strictly tenant/user-scoped at the query level, not just filtered client-side after the fact.
- [ ] Embedding model version is tracked per chunk; a model upgrade triggers re-embedding, not silent dimension mismatches.
- [ ] Token budget enforced on context construction so prompts never silently exceed the model's context window.
- [ ] Citations are verifiable — every claim in the answer maps to a retrievable chunk ID, not fabricated post hoc.
- [ ] Cost and token usage logged per query and aggregable per tenant for billing/budget alerts.
- [ ] Streaming responses handle client disconnects cleanly (stop generation, don't leak the request).
- [ ] Vector index rebuild/maintenance strategy documented (ivfflat/HNSW need periodic tuning as data grows).
- [ ] "Insufficient context" path tested explicitly — the system must be able to say "I don't know" instead of hallucinating.
- [ ] Rate limiting and per-tenant quota on `/query` to control LLM spend, per [AI rate limits](../../docs/15-production-ai-systems/ai-rate-limits.md).
- [ ] Ingestion pipeline retries transient embedding-provider failures with backoff, per [Project 5](../05-document-processing/README.md)'s pattern.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Builds on: [Project 5 — Async Document Processing Pipeline](../05-document-processing/README.md)
- Pairs with: [Project 8 — Multi-Provider LLM Gateway](../08-llm-gateway/README.md)
