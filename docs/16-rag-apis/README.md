# Part 16 — RAG APIs

## What You'll Learn

The complete Retrieval-Augmented Generation lifecycle as an API engineering problem: document ingestion APIs, file upload architecture, chunking pipelines, embedding APIs, vector database APIs, retrieval, reranking, context construction, streaming RAG responses, and async document processing.

```text
Document Upload → Object Storage → Background Job → Parsing → Chunking
   → Embeddings → Vector Database → Retrieval → Reranking
   → Context Construction → LLM → Streaming Response
```

## Prerequisites

[Part 14 — AI API Engineering](../14-ai-api-engineering/README.md), [Part 8 — Async Systems](../08-async-systems/README.md) (ingestion is a background-job problem).

## Chapters

| # | Chapter | Status |
|---|---|---|
| 1 | [Document Ingestion APIs](document-ingestion-apis.md) | ✅ Written |
| 2 | [File Upload Architecture](file-upload-architecture.md) | ✅ Written |
| 3 | [Chunking Pipelines](chunking-pipelines.md) | ✅ Written |
| 4 | [Embedding APIs](embedding-apis.md) | ✅ Written |
| 5 | [Vector Database APIs](vector-database-apis.md) | ✅ Written |
| 6 | [Retrieval](retrieval.md) | ✅ Written |
| 7 | [Reranking](reranking.md) | ✅ Written |
| 8 | [Context Construction](context-construction.md) | ✅ Written |
| 9 | [Streaming RAG](streaming-rag.md) | ✅ Written |
| 10 | [Async Document Processing](async-document-processing.md) | ✅ Written |

## Related Example

[`examples/rag-api/`](../../examples/rag-api/) — a minimal end-to-end RAG pipeline.

## Related Project

[Project 7 — Production RAG API](../../projects/07-production-rag/).

## Next

[Part 17 — AI Agents & MCP](../17-ai-agents-and-mcp/README.md)
