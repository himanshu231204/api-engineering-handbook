# RAG (Retrieval-Augmented Generation) Cheatsheet

For the full explanation, see [RAG APIs](../../docs/16-rag-apis/README.md).

## Pipeline stages, one line each

1. **Document ingestion** — accept raw documents (PDF, HTML, markdown, etc.) via an upload API or connector.
2. **Parsing/extraction** — pull clean text (and structure like tables/headings) out of the raw file format.
3. **Chunking** — split the text into smaller, retrievable pieces sized for the embedding model and context window.
4. **Embedding** — convert each chunk into a vector via an embedding model API.
5. **Indexing/storage** — store vectors + metadata in a vector database for fast similarity search.
6. **Query embedding** — embed the user's query with the same embedding model used for chunks.
7. **Retrieval** — find the top-K most similar chunks to the query vector (approximate nearest neighbor search).
8. **Reranking** *(optional)* — re-score retrieved chunks with a more precise (often cross-encoder) model to improve ordering.
9. **Context construction** — assemble the final chunks into a prompt, respecting token budget and citing sources.
10. **Generation** — send the constructed prompt to the LLM, optionally streaming the response back to the user.

## Chunking strategy comparison

| Strategy | How it works | Pros | Cons | Best for |
|---|---|---|---|---|
| **Fixed-size (character/token count)** | Split every N tokens/characters, often with overlap | Simple, predictable, fast | Can cut sentences/ideas mid-thought | Quick prototypes, uniform text |
| **Sentence/paragraph-based** | Split on natural sentence or paragraph boundaries | Preserves semantic units | Uneven chunk sizes | General prose, articles, docs |
| **Recursive/structure-aware** | Split by document structure hierarchy (headings → paragraphs → sentences), falling back to smaller units as needed | Respects document structure, good balance of size and coherence | More implementation complexity | Markdown/HTML docs, technical documentation |
| **Semantic chunking** | Split at points where embedding similarity between adjacent sentences drops (topic shifts) | Chunks align with actual topic boundaries | Computationally expensive (embeds during chunking), less predictable size | High-value corpora where retrieval quality matters most |
| **Sliding window with overlap** | Fixed-size chunks that overlap by N tokens with neighbors | Reduces the "cut off mid-idea" problem of fixed-size | More stored chunks (redundancy), more storage/embedding cost | Dense technical text where context continuity matters |

Typical starting point: 200–500 tokens per chunk with 10–20% overlap — then tune based on retrieval quality.

## Retrieval quality quick tips

- **Use hybrid search** (dense vector similarity + sparse keyword/BM25) — vector search alone misses exact-match terms (IDs, acronyms, product names).
- **Always rerank when precision matters** — initial vector retrieval optimizes for recall (fast, approximate); a reranker fixes ordering with a slower, more accurate model.
- **Attach metadata filters** (date, source, category, tenant ID) to narrow the search space before or during similarity search — don't rely on the LLM to ignore irrelevant results.
- **Chunk size is a tradeoff**: smaller chunks → more precise retrieval but less context per chunk; larger chunks → more context but noisier matches.
- **Evaluate retrieval separately from generation** — measure recall@K and precision@K on a labeled query set before blaming the LLM for bad answers.
- **Cite sources** — include chunk provenance (document, page, section) in the context so the model can cite it and you can debug bad answers.
- **Watch for "lost in the middle"** — LLMs attend less reliably to content in the middle of a very long context; put the most relevant chunks near the start or end of the constructed prompt.
- **Guard against context overflow** — always compute the token budget for retrieved chunks + system prompt + query before sending to the LLM.
