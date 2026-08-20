"""
Embeddings + an in-memory vector store for the RAG example.

Two things live here:

1. `embed()` — turns text into a vector. If `EMBEDDING_API_KEY` is set in
   the environment, it points at `_embed_via_api`, a clearly-commented
   pseudo-implementation showing the shape of a real embedding API call
   (see ../../docs/16-rag-apis/embedding-apis.md). Otherwise it falls back
   to `_embed_local_bag_of_words`, a tiny dependency-free bag-of-words/
   feature-hashing embedding — good enough to demonstrate retrieval working
   correctly, not good enough for production semantic search. This fallback
   is what makes the example runnable end-to-end with zero API keys.

2. `VectorStore` — an in-memory list of (id, text, vector, metadata) plus
   brute-force cosine-similarity search. No external vector database
   required. See ../../docs/16-rag-apis/vector-database-apis.md for how to
   swap this for a real vector DB (pgvector, Pinecone, Qdrant, etc.) once
   you outgrow "everything fits in one process's memory."
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass, field

EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "example-embedding-v1")

# Dimensionality of the local fallback embedding. Arbitrary — just needs to
# be consistent between ingested chunks and queries.
LOCAL_EMBEDDING_DIM = 256

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def embed(text: str) -> list[float]:
    """Embed `text` into a fixed-length vector.

    Uses a real embedding API if `EMBEDDING_API_KEY` is configured,
    otherwise falls back to a local bag-of-words embedding so this example
    runs without any external credentials.
    """
    if EMBEDDING_API_KEY:
        return _embed_via_api(text)
    return _embed_local_bag_of_words(text)


def _embed_via_api(text: str) -> list[float]:
    """Illustrative pseudo-implementation of a real embedding API call.

    Not wired up to any specific provider's SDK, since we can't assume
    which one you have credentials for. The general shape, using `httpx` as
    a generic HTTP client, looks like:

        import httpx

        response = httpx.post(
            "https://api.your-provider.example/v1/embeddings",
            headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
            json={"model": EMBEDDING_MODEL, "input": text},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    See ../../docs/16-rag-apis/embedding-apis.md for the full pattern,
    including batching multiple chunks into one request to reduce latency
    and cost.
    """
    raise NotImplementedError(
        "EMBEDDING_API_KEY is set, but _embed_via_api() is still a stub. "
        "Plug in a real provider SDK/HTTP call here, following the shape "
        "described in this function's docstring."
    )


def _embed_local_bag_of_words(text: str, dim: int = LOCAL_EMBEDDING_DIM) -> list[float]:
    """A tiny, dependency-free stand-in for a real embedding model.

    Tokenizes text, hashes each token into one of `dim` buckets (the
    "hashing trick" — avoids needing a fixed vocabulary), counts term
    frequency per bucket, and L2-normalizes the result so cosine similarity
    behaves sensibly. This captures simple keyword overlap between texts —
    nothing like the semantic understanding of a real embedding model — but
    it's enough to demonstrate the retrieval pipeline working end-to-end
    with zero external dependencies or API keys.
    """
    vector = [0.0] * dim
    tokens = _TOKEN_RE.findall(text.lower())

    for token in tokens:
        # A stable hash (unlike Python's randomized `hash()`) so the same
        # token always maps to the same bucket across runs/processes.
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        bucket = int(digest, 16) % dim
        vector[bucket] += 1.0

    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class StoredChunk:
    id: str
    text: str
    vector: list[float]
    source: str
    chunk_index: int


@dataclass
class VectorStore:
    """A brute-force, in-memory vector store.

    Fine for a demo (or a few thousand chunks); does a full linear scan on
    every query. Real deployments use an actual vector database (pgvector,
    Pinecone, Qdrant, Weaviate, ...) with an approximate-nearest-neighbor
    index so search stays fast at millions of vectors — see
    ../../docs/16-rag-apis/vector-database-apis.md.
    """

    _chunks: list[StoredChunk] = field(default_factory=list)

    def add(self, *, id: str, text: str, source: str, chunk_index: int) -> None:
        vector = embed(text)
        self._chunks.append(
            StoredChunk(id=id, text=text, vector=vector, source=source, chunk_index=chunk_index)
        )

    def search(self, query: str, *, top_k: int = 3) -> list[tuple[StoredChunk, float]]:
        """Return the `top_k` stored chunks most similar to `query`,
        as (chunk, score) pairs sorted by descending similarity."""
        if not self._chunks:
            return []

        query_vector = embed(query)
        scored = [
            (chunk, cosine_similarity(query_vector, chunk.vector))
            for chunk in self._chunks
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]

    def __len__(self) -> int:
        return len(self._chunks)
